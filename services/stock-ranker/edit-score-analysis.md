# Plan: Add Edit Score Feature (within Wizard)

## Context

The wizard now supports editing an analysis (name + scores list) via the Edit button added in the previous session. However, individual scores within the draft list cannot be modified — only removed and re-added from scratch. This plan adds an inline "edit score" flow: clicking a pencil button on a draft score populates the scoreForm for editing; submitting replaces the score in-place rather than appending a new one.

## Critical File

- `src/stock_ranker/server/static/index.html` — only file to change

## Changes (5 targeted edits)

### 1. Add `editingScoreIndex` to wizard state (~line 703)

Add after `scoreForm`:

```js
// Before
scoreForm: { name: '', expression: '', normalize: false },

// After
scoreForm: { name: '', expression: '', normalize: false },
editingScoreIndex: null,   // null = add mode, int = edit mode
```

### 2. Reset `editingScoreIndex` in `openWizard()` (~line 882)

```js
// After the scoreForm reset line:
this.wizard.scoreForm = { name: '', expression: '', normalize: false };
this.wizard.editingScoreIndex = null;   // ← add this line
```

### 3. Add Edit button to each score-item in the draft list (~line 371)

Current score-item template:
```html
<button class="chip-remove" @click="wizard.draft.scores.splice(i,1)" title="Remove">×</button>
```

Insert an edit button before the remove button:
```html
<button class="chip-remove" @click="editScore(i)" title="Edit" style="font-size:.95rem;">✎</button>
<button class="chip-remove" @click="wizard.draft.scores.splice(i,1)" title="Remove">×</button>
```

### 4. Add `editScore(i)` function and modify `addScoreToDraft()` (~line 906)

Add new function right before `addScoreToDraft`:
```js
editScore(i) {
  const s = this.wizard.draft.scores[i];
  this.wizard.scoreForm = { name: s.name, expression: s.expression, normalize: s.normalize };
  this.wizard.editingScoreIndex = i;
  this.wizard.scoreError = null;
},
```

Modify `addScoreToDraft()` to handle both modes:
```js
addScoreToDraft() {
  this.wizard.scoreError = null;
  const sf = this.wizard.scoreForm;
  if (!sf.name.trim()) { this.wizard.scoreError = 'Score name is required.'; return; }
  if (!sf.expression.trim()) { this.wizard.scoreError = 'Expression is required.'; return; }
  const score = { name: sf.name.trim(), expression: sf.expression.trim(), normalize: sf.normalize };
  if (this.wizard.editingScoreIndex !== null) {
    this.wizard.draft.scores[this.wizard.editingScoreIndex] = score;
    this.wizard.editingScoreIndex = null;
  } else {
    this.wizard.draft.scores.push(score);
  }
  this.wizard.scoreForm = { name: '', expression: '', normalize: false };
},
```

### 5. Dynamic label on the "Add score" button (~line 410)

```html
<!-- Before -->
<button class="btn btn-outline" type="button" @click="addScoreToDraft()">+ Add score</button>

<!-- After -->
<button class="btn btn-outline" type="button" @click="addScoreToDraft()">
  <span x-text="wizard.editingScoreIndex !== null ? 'Update score' : '+ Add score'"></span>
</button>
```
