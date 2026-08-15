const chatOutput = document.getElementById('chat-output');
const docList = document.getElementById('doc-list');
const demoList = document.getElementById('demo-list');
const demoSelectionCount = document.getElementById('demo-selection-count');
const questionInput = document.getElementById('question-input');
const queryForm = document.getElementById('query-form');
const fileInput = document.getElementById('file-input');
const statusPill = document.getElementById('status-pill');
const loadDemoButton = document.getElementById('load-demo');
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

async function refreshDocuments() {
  const response = await fetch('/api/documents');
  const data = await response.json();
  docList.innerHTML = '';
  if (!data.documents || data.documents.length === 0) {
    const item = document.createElement('li');
    item.textContent = 'No documents loaded yet';
    docList.appendChild(item);
    return;
  }

  data.documents.forEach((doc) => {
    const li = document.createElement('li');
    li.textContent = doc.name;
    docList.appendChild(li);
  });
}

async function refreshDemoDocuments() {
  const response = await fetch('/api/demo-documents');
  const data = await response.json();
  demoList.innerHTML = '';
  data.documents.forEach((doc) => {
    const item = document.createElement('li');
    const label = document.createElement('label');
    label.className = 'demo-option';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = doc.name;
    checkbox.checked = true;
    checkbox.addEventListener('change', updateDemoSelectionCount);
    const name = document.createElement('span');
    name.textContent = doc.name;
    label.append(checkbox, name);
    item.appendChild(label);
    demoList.appendChild(item);
  });
  updateDemoSelectionCount();
}

function updateDemoSelectionCount() {
  const selected = demoList.querySelectorAll('input[type="checkbox"]:checked').length;
  demoSelectionCount.textContent = `${selected} selected`;
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
      await refreshDocuments();
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
    await refreshDocuments();
    addMessage('assistant', `Loaded ${data.documents.length} selected demo document(s). Ask a question about their content.`);
    setStatus('Ready', 'idle');
  } catch (error) {
    addMessage('assistant', 'The demo set could not be loaded.');
    setStatus('Error', 'error');
  }
});

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

refreshDocuments();
refreshDemoDocuments();
