const chatOutput = document.getElementById('chat-output');
const demoList = document.getElementById('demo-list');
const demoSelectionCount = document.getElementById('demo-selection-count');
const questionInput = document.getElementById('question-input');
const queryForm = document.getElementById('query-form');
const fileInput = document.getElementById('file-input');
const statusPill = document.getElementById('status-pill');
const loadDemoButton = document.getElementById('load-demo');
const selectAllDemoButton = document.getElementById('select-all-demo');
const clearAllDemoButton = document.getElementById('clear-all-demo');
const generateBriefButton = document.getElementById('generate-brief');

function setStatus(text, variant = 'idle') {
  statusPill.textContent = text;
  statusPill.className = `status-pill status-${variant}`;
}

function addMessage(role, text) {
  const wrapper = document.createElement('div');
  wrapper.className = role === 'assistant' ? 'assistant-message' : 'user-message';
  const p = document.createElement('p');
  p.textContent = text;
  wrapper.appendChild(p);
  chatOutput.appendChild(wrapper);
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function addTrace(result) {
  const trace = document.createElement('div');
  trace.className = 'retrieval-trace';
  const sources = (result.sources || []).join(', ') || 'No source matched';
  const retrieval = result.retrieval || {};
  trace.textContent = `${result.provider || 'retrieval'} · ${retrieval.retrieved_chunks || 0} chunks retrieved · sources: ${sources}`;
  chatOutput.appendChild(trace);
}

async function refreshDemoDocuments() {
  demoList.innerHTML = '<li class="demo-list-status">Loading demo documents…</li>';
  try {
    const response = await fetch('/api/demo-documents');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    demoList.innerHTML = '';
    if (!data.documents.length) {
      demoList.innerHTML = '<li class="demo-list-status">No demo documents found.</li>';
      updateDemoSelectionCount();
      return;
    }
    data.documents.forEach((doc) => {
      const item = document.createElement('li');
      const label = document.createElement('label');
      label.className = 'demo-option';
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = doc.name;
      checkbox.checked = true;
      checkbox.setAttribute('aria-label', `Select ${doc.name}`);
      checkbox.addEventListener('change', () => {
        updateDemoOptionState(label, checkbox);
        updateDemoSelectionCount();
      });
      const name = document.createElement('span');
      name.textContent = doc.name;
      const state = document.createElement('strong');
      state.className = 'demo-option-state';
      label.append(checkbox, name, state);
      updateDemoOptionState(label, checkbox);
      item.appendChild(label);
      demoList.appendChild(item);
    });
    updateDemoSelectionCount();
  } catch (error) {
    demoList.innerHTML = '<li class="demo-list-status error">Demo documents could not be loaded. Refresh the page or check the server.</li>';
    demoSelectionCount.textContent = 'Unavailable';
  }
}

function updateDemoOptionState(label, checkbox) {
  label.classList.toggle('selected', checkbox.checked);
  label.querySelector('.demo-option-state').textContent = checkbox.checked ? 'Selected' : 'Not selected';
}

function updateDemoSelectionCount() {
  const selected = demoList.querySelectorAll('input[type="checkbox"]:checked').length;
  demoSelectionCount.textContent = `${selected} selected`;
}

function setDemoSelection(checked) {
  demoList.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.checked = checked;
    updateDemoOptionState(checkbox.closest('.demo-option'), checkbox);
  });
  updateDemoSelectionCount();
}

queryForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage('user', question);
  questionInput.value = '';
  setStatus('Thinking…', 'busy');

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const payload = await response.json();
    const answer = payload.answer || 'No answer returned.';
    addMessage('assistant', answer);
    addTrace(payload);
    setStatus('Ready', 'idle');
  } catch (error) {
    addMessage('assistant', 'There was an error processing this question. Please try again.');
    setStatus('Error', 'error');
  }
});

fileInput.addEventListener('change', async (event) => {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;

  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  setStatus('Uploading…', 'busy');

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    if (data.status === 'ok') {
      addMessage('assistant', `Uploaded ${data.added.length} document(s): ${data.added.join(', ')}`);
      setStatus('Ready', 'idle');
    }
  } catch (error) {
    addMessage('assistant', 'Upload failed. Please ensure the documents are valid text, PDF, or Markdown files.');
    setStatus('Error', 'error');
  } finally {
    fileInput.value = '';
  }
});

loadDemoButton.addEventListener('click', async () => {
  const selectedDocuments = Array.from(demoList.querySelectorAll('input[type="checkbox"]:checked'))
    .map((checkbox) => checkbox.value);
  if (!selectedDocuments.length) {
    addMessage('assistant', 'Select at least one demo document before loading the library.');
    return;
  }
  setStatus('Loading demo…', 'busy');
  try {
    const response = await fetch('/api/load-demo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents: selectedDocuments }),
    });
    const data = await response.json();
    addMessage('assistant', `Loaded ${data.documents.length} selected demo document(s). The highlighted rows are now the active retrieval set.`);
    setStatus('Ready', 'idle');
  } catch (error) {
    addMessage('assistant', 'The demo set could not be loaded.');
    setStatus('Error', 'error');
  }
});

selectAllDemoButton.addEventListener('click', () => setDemoSelection(true));
clearAllDemoButton.addEventListener('click', () => setDemoSelection(false));

generateBriefButton.addEventListener('click', async () => {
  setStatus('Generating brief…', 'busy');
  generateBriefButton.disabled = true;
  try {
    const response = await fetch('/api/brief', { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Gemini is unavailable');
    addMessage('assistant', data.brief);
    addTrace({ provider: data.provider, sources: data.sources, retrieval: { retrieved_chunks: 'library' } });
    setStatus('Ready', 'idle');
  } catch (error) {
    addMessage('assistant', `AI brief unavailable: ${error.message}. The core retrieval experience still works without Gemini.`);
    setStatus('AI unavailable', 'error');
  } finally {
    generateBriefButton.disabled = false;
  }
});

refreshDemoDocuments();
