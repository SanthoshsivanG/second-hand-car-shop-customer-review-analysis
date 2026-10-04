-- Dashboard Postgres schema
-- Loaded automatically by the postgres Docker image on first start.

CREATE TABLE IF NOT EXISTS idea_policy (
    id          SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    content     TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE idea_policy IS 'Single active AI idea-generation policy (always id=1).';

CREATE TABLE IF NOT EXISTS generated_ideas (
    id              BIGSERIAL PRIMARY KEY,
    journey         TEXT NOT NULL,
    topic           TEXT NOT NULL,
    satisfaction    TEXT NOT NULL CHECK (satisfaction IN ('positive', 'negative')),
    mode            TEXT NOT NULL CHECK (mode IN ('keep', 'improve')),
    store_names     JSONB NOT NULL DEFAULT '[]'::jsonb,
    ideas           JSONB NOT NULL,
    comments        JSONB NOT NULL,
    policy_version  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_ideas_lookup
    ON generated_ideas (journey, topic, satisfaction, created_at DESC);

COMMENT ON TABLE generated_ideas IS 'Stored AI keep/improve idea generations with source comments.';

-- Seed default policy once (id=1). Edit later via API / dashboard.
INSERT INTO idea_policy (id, content)
VALUES (
    1,
    $policy$# Idea generation policy

Edit this text in the dashboard (Policy editor) to control how the AI writes suggestions.
It is stored in the `idea_policy` Postgres table.

## Role
You are an advisor for a second-hand car dealership analyzing customer reviews.

## Output rules
- Write in clear, simple English.
- Give 4 to 6 concrete bullet points.
- Each bullet should be actionable and specific to the dealership context.
- Do not invent facts that are not supported by the sample comments.
- Do not mention that you are an AI.
- Do not include greetings or closing fluff.
- Keep each bullet under 25 words when possible.

## When sentiment is negative (improvement ideas)
- Focus on what to fix or improve.
- Prioritize frequent pain points in the samples.
- Prefer operational changes (process, training, communication, timing, follow-up).

## When sentiment is positive (points to keep)
- Focus on strengths to protect and repeat.
- Name the behaviors/processes that customers praised.
- Suggest how to standardize or scale those strengths.

## Style
- Neutral, professional tone.
- No marketing hype.
- No personal data speculation.
$policy$
)
ON CONFLICT (id) DO NOTHING;
