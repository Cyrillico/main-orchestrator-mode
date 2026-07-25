export const meta = {
  name: 'main-orchestrator-mode',
  description:
    'Main Orchestrator Mode: parallel read-only subagents, exclusive same-file write locks, summary-only returns; parent never loads long context; parent polls active workers ~every 3 min to recover stalls',
  whenToUse:
    'Invoked by /orch or when multi-file work needs parallel explore + file-locked writes with short digests',
  phases: [
    { title: 'Plan', detail: 'Split tasks with read/write file sets' },
    { title: 'Read', detail: 'Parallel read-only workers; parent watchdog poll ~3 min' },
    { title: 'Write', detail: 'File-locked exclusive write batches; parent watchdog poll ~3 min' },
    { title: 'Verify', detail: 'Acceptance checks; parent watchdog poll ~3 min' },
    { title: 'Synthesize', detail: 'Merge digests only; no long reads' },
  ],
}

// args may be object or JSON/string goal
const ARGS =
  typeof args === 'string'
    ? (() => {
        try {
          return JSON.parse(args)
        } catch (e) {
          return { goal: args }
        }
      })()
    : args || {}

const USER_GOAL = String(
  (ARGS && (ARGS.goal || ARGS.prompt || ARGS.ARGUMENTS)) || '',
).trim()

if (!USER_GOAL) {
  return {
    final: {
      accepted: false,
      summary: 'Missing goal. Pass args: { goal: "..." }',
      changed_files: [],
      residual_risks: ['empty goal'],
    },
    task_count: 0,
    completed_ids: [],
    digests: [],
  }
}

const AGENT_PREFIX = `
[ROLE] Subagent under Main Orchestrator Mode.
[HARD RULES]
1. Execute local work only; do not coordinate other agents.
2. Return ONLY schema fields; no free-form dumps.
3. NEVER return full source, full diffs, long logs, or transcripts.
4. key_changes ≤ 8 one-line bullets; minimal_snippets default empty (≤2, ≤20 lines if unavoidable).
5. WRITE: only touch granted write_files. READ: no edits.
6. Prefer path + line hints over code paste.
[OUTPUT] Short structured summary only.
`.trim()

const SUMMARY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: [
    'status',
    'goal',
    'conclusion',
    'read_files',
    'write_files',
    'key_changes',
    'risks',
    'blockers',
    'next_suggestion',
  ],
  properties: {
    status: {
      type: 'string',
      enum: ['done', 'partial', 'blocked', 'noop'],
    },
    goal: { type: 'string', maxLength: 200 },
    conclusion: { type: 'string', maxLength: 500 },
    read_files: {
      type: 'array',
      maxItems: 30,
      items: { type: 'string', maxLength: 260 },
    },
    write_files: {
      type: 'array',
      maxItems: 20,
      items: { type: 'string', maxLength: 260 },
    },
    key_changes: {
      type: 'array',
      maxItems: 8,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'summary'],
        properties: {
          file: { type: 'string', maxLength: 260 },
          summary: { type: 'string', maxLength: 160 },
          lines_hint: { type: 'string', maxLength: 40 },
        },
      },
    },
    risks: {
      type: 'array',
      maxItems: 5,
      items: { type: 'string', maxLength: 160 },
    },
    blockers: {
      type: 'array',
      maxItems: 5,
      items: { type: 'string', maxLength: 160 },
    },
    next_suggestion: { type: 'string', maxLength: 240 },
    minimal_snippets: {
      type: 'array',
      maxItems: 2,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'lines_hint', 'snippet'],
        properties: {
          file: { type: 'string', maxLength: 260 },
          lines_hint: { type: 'string', maxLength: 40 },
          snippet: { type: 'string', maxLength: 800 },
        },
      },
    },
  },
}

const PLAN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['tasks'],
  properties: {
    tasks: {
      type: 'array',
      maxItems: 40,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'kind', 'goal', 'read_files', 'write_files'],
        properties: {
          id: { type: 'string', maxLength: 40 },
          kind: { type: 'string', enum: ['read', 'write', 'verify'] },
          goal: { type: 'string', maxLength: 240 },
          read_files: {
            type: 'array',
            maxItems: 20,
            items: { type: 'string', maxLength: 260 },
          },
          write_files: {
            type: 'array',
            maxItems: 10,
            items: { type: 'string', maxLength: 260 },
          },
          depends_on: {
            type: 'array',
            maxItems: 10,
            items: { type: 'string', maxLength: 40 },
          },
          agent_type: {
            type: 'string',
            enum: ['Explore', 'general-purpose', 'claude'],
          },
        },
      },
    },
  },
}

const FINAL_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['accepted', 'summary', 'changed_files', 'residual_risks'],
  properties: {
    accepted: { type: 'boolean' },
    summary: { type: 'string', maxLength: 800 },
    changed_files: {
      type: 'array',
      maxItems: 50,
      items: { type: 'string', maxLength: 260 },
    },
    residual_risks: {
      type: 'array',
      maxItems: 10,
      items: { type: 'string', maxLength: 160 },
    },
  },
}

function normalizePath(p) {
  return String(p || '')
    .replace(/\\/g, '/')
    .replace(/^\.\//, '')
}

function partitionWriteTasks(tasks) {
  const batches = []
  const remaining = tasks.map(t => ({
    ...t,
    write_files: (t.write_files || []).map(normalizePath),
  }))

  while (remaining.length) {
    const batch = []
    const locked = new Set()
    for (let i = 0; i < remaining.length; ) {
      const t = remaining[i]
      const files = t.write_files || []
      const conflict = files.some(f => locked.has(f))
      if (!conflict) {
        files.forEach(f => locked.add(f))
        batch.push(t)
        remaining.splice(i, 1)
      } else {
        i++
      }
    }
    if (!batch.length && remaining.length) {
      batch.push(remaining.shift())
    }
    batches.push(batch)
  }
  return batches
}

function readyTasks(tasks, doneIds) {
  return tasks.filter(t => (t.depends_on || []).every(d => doneIds.has(d)))
}

function taskPrompt(t, kindExtra, done) {
  const prior = (t.depends_on || [])
    .map(id => done.get(id))
    .filter(Boolean)
    .map(s => `- [${s.status}] ${s.goal}: ${s.conclusion}`)
    .join('\n')

  return `${AGENT_PREFIX}

[TASK id=${t.id} kind=${t.kind}]
Goal: ${t.goal}
Granted read_files: ${JSON.stringify(t.read_files || [])}
Granted write_files: ${JSON.stringify(t.write_files || [])}
${kindExtra || ''}

Prior dependency summaries (do not re-read full code unless granted):
${prior || '(none)'}

User overall goal:
${USER_GOAL}
`
}

phase('Plan')
log(`Orchestrator goal: ${USER_GOAL}`)

const plan = await agent(
  `${AGENT_PREFIX}

[TASK kind=plan]
You are the planner for Main Orchestrator Mode.
User goal:
${USER_GOAL}

Produce a task list only:
- Split into read / write / verify tasks
- Each task MUST list read_files and write_files (paths only; may be empty if unknown — then use broad search in read)
- Prefer many small read tasks that can run in parallel
- write tasks MUST declare exact write_files when known (for exclusive locks); if unknown, put discovery in read first
- Keep goals short; do not open or return file contents
- Mark depends_on when write/verify needs prior read conclusions
- Prefer agent_type Explore for read; general-purpose for write/verify
`,
  {
    label: 'plan',
    phase: 'Plan',
    schema: PLAN_SCHEMA,
    effort: 'medium',
  },
)

if (!plan || !plan.tasks || !plan.tasks.length) {
  return {
    final: {
      accepted: false,
      summary: 'Plan phase returned empty tasks',
      changed_files: [],
      residual_risks: ['planner returned null/empty'],
    },
    task_count: 0,
    completed_ids: [],
    digests: [],
  }
}

const allTasks = plan.tasks
const done = new Map()
const doneIds = new Set()

// ---------- READ ----------
// Parent watchdog: while workers run, poll status ~every 3 min (2-5).
// Alive = any activity. Bare wait-timeout != dead. One progress nudge if silent;
// reassign after nudge + another silent interval.
phase('Read')
const readTasks = allTasks.filter(t => t.kind === 'read')
if (readTasks.length) {
  const readResults = await parallel(
    readTasks.map(t => () =>
      agent(taskPrompt(t, '[READ-ONLY] No file mutations allowed.', done), {
        label: `read:${t.id}`,
        phase: 'Read',
        schema: SUMMARY_SCHEMA,
        agentType: t.agent_type === 'claude' ? 'claude' : 'Explore',
        effort: 'low',
      }).then(s => ({ id: t.id, summary: s })),
    ),
  )
  for (const r of readResults.filter(Boolean)) {
    if (r.summary) {
      done.set(r.id, r.summary)
      doneIds.add(r.id)
    }
  }
  log(`Read done: ${[...doneIds].filter(id => readTasks.some(t => t.id === id)).length}/${readTasks.length}`)
}

// ---------- WRITE ----------
// Parent watchdog applies to write batches the same as read (poll / nudge / reassign).
phase('Write')
let writePool = allTasks.filter(t => t.kind === 'write')
let guard = 0
while (writePool.length && guard++ < 50) {
  const ready = readyTasks(writePool, doneIds)
  if (!ready.length) {
    log(
      'Write deadlock/unsatisfied depends_on; remaining: ' +
        writePool.map(t => t.id).join(','),
    )
    break
  }
  const batches = partitionWriteTasks(ready)
  const batch = batches[0]
  const lockList = [
    ...new Set(batch.flatMap(t => (t.write_files || []).map(normalizePath))),
  ].join('|')
  log(`Write batch: ${batch.map(t => t.id).join(', ')} locks=${lockList || '(none)'}`)

  const writeResults = await parallel(
    batch.map(t => () =>
      agent(
        taskPrompt(
          t,
          '[WRITE LOCK GRANTED] You are the sole writer for granted write_files this batch. Do not modify other paths.',
          done,
        ),
        {
          label: `write:${t.id}`,
          phase: 'Write',
          schema: SUMMARY_SCHEMA,
          agentType:
            t.agent_type === 'Explore'
              ? 'general-purpose'
              : t.agent_type || 'general-purpose',
          effort: 'medium',
        },
      ).then(s => ({ id: t.id, summary: s })),
    ),
  )

  for (const r of writeResults.filter(Boolean)) {
    if (r.summary) {
      done.set(r.id, r.summary)
      doneIds.add(r.id)
    }
  }
  writePool = writePool.filter(t => !doneIds.has(t.id))
}

// ---------- VERIFY ----------
phase('Verify')
const verifyTasks = allTasks.filter(t => t.kind === 'verify')
if (verifyTasks.length) {
  const readyVerify = readyTasks(verifyTasks, doneIds)
  if (readyVerify.length) {
    const verifyResults = await parallel(
      readyVerify.map(t => () =>
        agent(
          taskPrompt(
            t,
            '[VERIFY] Confirm acceptance criteria. Prefer tests/commands over re-reading entire modules.',
            done,
          ),
          {
            label: `verify:${t.id}`,
            phase: 'Verify',
            schema: SUMMARY_SCHEMA,
            agentType: t.agent_type || 'general-purpose',
            effort: 'medium',
          },
        ).then(s => ({ id: t.id, summary: s })),
      ),
    )
    for (const r of verifyResults.filter(Boolean)) {
      if (r.summary) {
        done.set(r.id, r.summary)
        doneIds.add(r.id)
      }
    }
  }
  const skipped = verifyTasks.filter(t => !doneIds.has(t.id))
  if (skipped.length) {
    log('Verify skipped (deps): ' + skipped.map(t => t.id).join(','))
  }
}

// ---------- SYNTHESIZE ----------
phase('Synthesize')
const digest = [...done.entries()].map(([id, s]) => ({
  id,
  status: s.status,
  goal: s.goal,
  conclusion: s.conclusion,
  write_files: s.write_files,
  key_changes: s.key_changes,
  risks: s.risks,
  blockers: s.blockers,
}))

const final = await agent(
  `${AGENT_PREFIX}

[TASK kind=synthesize]
You are the Main Orchestrator synthesizer.
You MUST NOT request or invent full file contents.
Decide acceptance ONLY from the digest below.
Parent context policy: if parent is already heavy, prefer digest-only synthesis (do not re-read sources).

User goal:
${USER_GOAL}

Digest JSON:
${JSON.stringify(digest)}

Return FINAL_SCHEMA: accepted, short summary, union of changed files, residual risks.
If any write/verify is blocked or partial with open blockers, accepted=false.
If plan had write tasks that never completed, accepted=false.
`,
  {
    label: 'synthesize',
    phase: 'Synthesize',
    schema: FINAL_SCHEMA,
    effort: 'low',
  },
)

return {
  final: final || {
    accepted: false,
    summary: 'synthesize failed',
    changed_files: [],
    residual_risks: ['synthesize null'],
  },
  task_count: allTasks.length,
  completed_ids: [...doneIds],
  digests: digest,
  incomplete_write_ids: allTasks
    .filter(t => t.kind === 'write' && !doneIds.has(t.id))
    .map(t => t.id),
}
