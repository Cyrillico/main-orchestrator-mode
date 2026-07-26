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
  const optsByLabel = new Map()
  const promptByLabel = new Map()
  const agent = async (prompt, opts) => {
    const label = opts.label
    spawned.push(label)
    optsByLabel.set(label, opts)
    promptByLabel.set(label, prompt)
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
    optsFor: label => optsByLabel.get(label) || {},
    promptFor: label => promptByLabel.get(label) || '',
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

// Two tasks sharing an id overwrote each other's digest: both ran, one write_files set
// vanished from changed_files, and the run still reported accepted.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'w1', kind: 'write', goal: 'first', read_files: [], write_files: ['src/a.ts'] },
        { id: 'w1', kind: 'write', goal: 'second', read_files: [], write_files: ['src/b.ts'] },
      ],
    },
    summaries: { w1: ok('w1', ['src/a.ts']) },
    finalOut: accept({ changed_files: ['src/a.ts'] }),
  })
  const out = await r.run()
  check('duplicate id spawns only one worker', r.spawned.filter(s => s === 'write:w1').length === 1, r.spawned)
  check(
    'duplicate id is reported as blocked',
    out.digests.some(d => d.id.startsWith('w1#dup') && d.status === 'blocked'),
    out.digests.map(d => [d.id, d.status]),
  )
  check('duplicate id forces reject', out.final.accepted === false, out.final)
}

// A read task must never carry a write grant, nor get a write-capable agent.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'r1', kind: 'read', goal: 'g', read_files: ['src/a.ts'], write_files: ['src/a.ts'], agent_type: 'claude' },
      ],
    },
    summaries: { r1: ok('r1') },
    finalOut: accept(),
  })
  await r.run()
  const o = r.optsFor('read:r1')
  check('read agent is always read-only', o.agentType === 'Explore', o.agentType)
  check(
    'read prompt carries no write grant',
    r.promptFor('read:r1').includes('Granted write_files: []'),
    r.promptFor('read:r1').split('\n').filter(l => l.includes('Granted')),
  )
}

// A worker's self-reported write_files must be checked against its grant.
{
  const r = makeRunner({
    plan: { tasks: [{ id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] }] },
    summaries: { w1: ok('w1', ['src/a.ts', '/etc/passwd']) },
    finalOut: accept({ changed_files: ['src/a.ts'] }),
  })
  const out = await r.run()
  check('out-of-grant self-report is blocked', out.digests[0].status === 'blocked', out.digests)
  check('out-of-grant self-report rejects the run', out.final.accepted === false, out.final)
  check('offending path named in blockers', out.digests[0].blockers.join(' ').includes('/etc/passwd'), out.digests[0].blockers)
}

// A read reporting any edit at all is out of role: its grant is empty.
{
  const r = makeRunner({
    plan: { tasks: [{ id: 'r1', kind: 'read', goal: 'g', read_files: ['src/a.ts'], write_files: [] }] },
    summaries: { r1: ok('r1', ['src/leaked.ts']) },
    finalOut: accept(),
  })
  const out = await r.run()
  check('read that reports an edit is blocked', out.digests[0].status === 'blocked', out.digests)
  check('read escalation rejects the run', out.final.accepted === false, out.final)
}

// Deadlocked / never-ready tasks must explain themselves in a digest.
{
  const r = makeRunner({
    plan: {
      tasks: [
        { id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'], depends_on: ['w2'] },
        { id: 'w2', kind: 'write', goal: 'g', read_files: [], write_files: ['src/b.ts'], depends_on: ['w1'] },
        { id: 'v1', kind: 'verify', goal: 'g', read_files: [], write_files: [], depends_on: ['w1'] },
      ],
    },
    summaries: {},
    finalOut: accept(),
  })
  const out = await r.run()
  const byId = Object.fromEntries(out.digests.map(d => [d.id, d]))
  check('cycle members get a digest', !!byId.w1 && !!byId.w2, out.digests.map(d => d.id))
  check('cycle digest names depends_on', (byId.w1 || {}).blockers.join(' ').includes('depends_on'), byId.w1)
  check('skipped verify gets a digest', ((byId.v1 || {}).status) === 'blocked', byId.v1)
  check('cycle rejects the run', out.final.accepted === false, out.final)
}

// A write-only plan is allowed, but the missing verify is reported.
{
  const r = makeRunner({
    plan: { tasks: [{ id: 'w1', kind: 'write', goal: 'g', read_files: [], write_files: ['src/a.ts'] }] },
    summaries: { w1: ok('w1', ['src/a.ts']) },
    finalOut: accept({ changed_files: ['src/a.ts'] }),
  })
  const out = await r.run()
  check('write-only plan still accepts', out.final.accepted === true, out.final)
  check(
    'missing verify surfaces as residual risk',
    out.final.residual_risks.some(x => x.includes('no verify task')),
    out.final.residual_risks,
  )
  check(
    'un-run grant audit surfaces as residual risk',
    out.final.residual_risks.some(x => x.includes('audit_write_grant')),
    out.final.residual_risks,
  )
}

console.log(failures ? `\n${failures} FAILURE(S)` : '\nall green')
process.exit(failures ? 1 : 0)
