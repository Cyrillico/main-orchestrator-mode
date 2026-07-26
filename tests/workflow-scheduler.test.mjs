#!/usr/bin/env node
// Regression tests for the Claude adapter's scheduler.
//
// Runs the REAL workflow script with stubbed Workflow-runtime globals instead of
// reimplementing its logic, so a change to the shipped file is what gets tested.
// The script uses top-level `return`, so it is evaluated as an async function body.
//
// Usage: node tests/workflow-scheduler.test.mjs [path-to-workflow-script]
//        (defaults to the adapter copy in this repo)

import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const SRC =
  process.argv[2] || resolve(REPO, 'adapters/claude/workflows/main-orchestrator-mode.js')
const src = readFileSync(SRC, 'utf8').replace('export const meta', 'const meta')

function makeRunner({ plan, summaries, finalOut }) {
  const spawned = []
  const logs = []
  const agent = async (prompt, opts) => {
    const label = opts.label
    spawned.push(label)
    if (label === 'plan') return plan
    if (label === 'synthesize') return finalOut
    const id = label.split(':')[1]
    return Object.prototype.hasOwnProperty.call(summaries, id) ? summaries[id] : null
  }
  const parallel = async thunks => {
    const out = []
    for (const t of thunks) {
      try {
        out.push(await t())
      } catch {
        out.push(null)
      }
    }
    return out
  }
  const log = m => logs.push(String(m))
  const phase = () => {}
  const fn = new Function(
    'agent',
    'parallel',
    'log',
    'phase',
    'args',
    'budget',
    `return (async () => {${src}})()`,
  )
  return {
    run: () => fn(agent, parallel, log, phase, { goal: 'test goal' }, { total: null }),
    spawned,
    logs,
  }
}

const ok = (id, files = []) => ({
  status: 'done',
  goal: id,
  conclusion: 'ok',
  read_files: [],
  write_files: files,
  key_changes: [],
  risks: [],
  blockers: [],
  next_suggestion: '',
  evidence: [{ kind: 'command', summary: 'ran tests' }],
})

const accept = extra => ({
  accepted: true,
  summary: 's',
  changed_files: [],
  residual_risks: [],
  incomplete: [],
  ...extra,
})

let failures = 0
function check(name, cond, detail) {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}`)
  if (!cond) {
    failures++
    if (detail !== undefined) console.log('        ', JSON.stringify(detail))
  }
}

// A read whose depends_on names another read must still run: one wave would drop it
// (successIds is empty in wave 1) and deadlock every write behind it.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'r1', kind: 'read', goal: 'g', read_files: [], write_files: [] },
        { id: 'r2', kind: 'read', goal: 'g', read_files: [], write_files: [], depends_on: ['r1'] },
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'], depends_on: ['r2'] },
      ],
    },
    summaries: { r1: ok('r1'), r2: ok('r2'), w1: ok('w1', ['src/a.ts']) },
    finalOut: accept({ changed_files: ['src/a.ts'] }),
  })
  const out = await r.run()
  check('read->read chain runs in wave 2', r.spawned.includes('read:r2'), r.spawned)
  check('write behind that read unlocks', r.spawned.includes('write:w1'), r.spawned)
  check('run accepted', out.final.accepted === true, out.final)
}

// Granted paths are guarded on every task kind, not just write_files.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'r1', kind: 'read', goal: 'g', read_files: ['/etc/shadow'], write_files: [] },
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] },
      ],
    },
    summaries: { w1: ok('w1', ['src/a.ts']) },
    finalOut: accept({ changed_files: ['src/a.ts'] }),
  })
  const out = await r.run()
  check('absolute read_files never reaches a worker', !r.spawned.includes('read:r1'), r.spawned)
  check(
    'offending read is blocked',
    out.digests.some(d => d.id === 'r1' && d.status === 'blocked'),
    out.digests,
  )
  check('open blocker forces reject', out.final.accepted === false, out.final)
}

// A verify task's write_files is a granted path too, and verify runs with write tools.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] },
        { id: 'v1', kind: 'verify', goal: 'g', read_files: [], write_files: ['/etc/hosts'], depends_on: ['w1'] },
      ],
    },
    summaries: { w1: ok('w1', ['src/a.ts']) },
    finalOut: accept(),
  })
  const out = await r.run()
  check('absolute verify write_files rejected', !r.spawned.includes('verify:v1'), r.spawned)
  check('run rejected', out.final.accepted === false, out.final)
}

// A worker that never returns a summary must not re-spawn until the shared batch
// guard drains, starving other batches.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] },
        { id: 'w2', kind: 'write', goal: 'g', read_files: [], write_files: ['src/b.ts'] },
      ],
    },
    summaries: { w2: ok('w2', ['src/b.ts']) }, // w1 returns null forever
    finalOut: accept(),
  })
  const out = await r.run()
  const attempts = r.spawned.filter(s => s === 'write:w1').length
  check('dead worker attempted exactly twice', attempts === 2, { attempts, spawned: r.spawned })
  check('abandoned write is incomplete', out.incomplete_write_ids.includes('w1'), out.incomplete_write_ids)
  check('run rejected', out.final.accepted === false, out.final)
  check('sibling write still succeeded', out.completed_ids.includes('w2'), out.completed_ids)
}

// A null synthesizer must not report "changed nothing" when writes landed.
{
  const r = makeRunner({
    plan: { tasks: [{ id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] }] },
    summaries: { w1: ok('w1', ['src/a.ts']) },
    finalOut: null,
  })
  const out = await r.run()
  check(
    'changed_files recovered from digests',
    JSON.stringify(out.final.changed_files) === '["src/a.ts"]',
    out.final,
  )
}

// Case-variant paths are the same lock on APFS/Windows.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/x.ts'] },
        { id: 'w2', kind: 'write', goal: 'g', read_files: [], write_files: ['src/X.ts'] },
      ],
    },
    summaries: { w1: ok('w1', ['src/x.ts']), w2: ok('w2', ['src/X.ts']) },
    finalOut: accept(),
  })
  await r.run()
  const batches = r.logs.filter(l => l.startsWith('Write batch:'))
  check('case variants never share a batch', batches.length === 2, batches)
}

console.log(failures ? `\n${failures} FAILURE(S)` : '\nall green')
process.exit(failures ? 1 : 0)
