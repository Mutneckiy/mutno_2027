'use strict';
const form = document.querySelector('#profile-form');
const status = document.querySelector('#form-status');
const submit = document.querySelector('#submit-button');
const result = document.querySelector('#result');
const oracleLoading = document.querySelector('#oracle-loading');
let questions = [];
let imageUrl;
const today = new Date();
document.querySelector('#birth-date').max = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

async function loadQuestions() {
  try {
    const response = await fetch('/api/questions');
    if (!response.ok) throw new Error('questions');
    ({ questions } = await response.json());
    const container = document.querySelector('#questions');
    container.replaceChildren();
    questions.forEach((question, index) => {
      const fieldset = document.createElement('fieldset');
      const legend = document.createElement('legend');
      legend.textContent = `${index + 1}. ${question.text}`;
      fieldset.append(legend);
      const options = document.createElement('div');
      options.className = 'options';
      question.options.forEach((text, value) => {
        const label = document.createElement('label');
        label.className = 'option';
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = question.id;
        radio.value = value;
        radio.required = true;
        label.append(radio, document.createTextNode(text));
        options.append(label);
      });
      fieldset.append(options);
      container.append(fieldset);
    });
    submit.disabled = false;
  } catch {
    document.querySelector('#questions').textContent = 'Не удалось загрузить вопросы. Обнови страницу, чтобы попробовать снова.';
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  submit.disabled = true;
  status.textContent = 'Обращаемся к оракулу…';
  status.classList.add('is-pending');
  submit.setAttribute('aria-busy', 'true');
  oracleLoading.hidden = false;
  result.hidden = true;
  const data = new FormData(form);
  const profile = {
    full_name: data.get('full_name').trim(),
    birth_date: data.get('birth_date'),
    wish: data.get('wish').trim(),
    answers: Object.fromEntries(questions.map(q => [q.id, Number(data.get(q.id))]))
  };
  try {
    const response = await fetch('/api/predictions', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile), signal: AbortSignal.timeout(100000)
    });
    if (!response.ok) {
      throw new Error(response.status === 422 ? 'Проверь имя, дату рождения и желание: нужны все пять ответов, а в желании — хотя бы 3 символа.' : 'Не получилось собрать послание. Попробуй ещё раз чуть позже.');
    }
    const prediction = await response.json();
    document.querySelector('#result-title').textContent = prediction.title;
    document.querySelector('#result-intro').textContent = prediction.intro;
    document.querySelector('#notice').textContent = prediction.notice;
    const symbols = prediction.symbolic_profile;
    const summary = document.querySelector('#symbolic-summary');
    summary.replaceChildren();
    if (symbols) {
      const labels = [
        symbols.western.sign,
        `${symbols.chinese.animal} · ${symbols.chinese.element}`,
        `Число пути ${symbols.numerology.life_path}`,
        `Личный год ${symbols.numerology.personal_year}`
      ];
      if (symbols.numerology.name_number !== null) {
        labels.push(`Число имени ${symbols.numerology.name_number}`);
      }
      labels.forEach(label => {
        const chip = document.createElement('span');
        chip.textContent = label;
        summary.append(chip);
      });
    }
    document.querySelector('#symbolic-method').textContent = symbols?.method || '';
    document.querySelector('.symbolic-method').hidden = !symbols;
    const chapters = document.querySelector('#chapters');
    chapters.replaceChildren();
    prediction.chapters.forEach(chapter => {
      const article = document.createElement('article');
      article.className = 'chapter';
      const h3 = document.createElement('h3');
      h3.textContent = chapter.title;
      const p = document.createElement('p');
      p.textContent = chapter.text;
      article.append(h3, p);
      chapters.append(article);
    });
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    imageUrl = URL.createObjectURL(new Blob([prediction.svg], { type: 'image/svg+xml' }));
    const image = document.querySelector('#talisman-image');
    image.src = imageUrl;
    image.alt = prediction.talisman.name;
    document.querySelector('#download').href = imageUrl;
    document.querySelector('#talisman-name').textContent = prediction.talisman.name;
    document.querySelector('#talisman-meaning').textContent = prediction.talisman.meaning;
    result.hidden = false;
    status.textContent = 'Твоё послание готово.';
    result.focus({ preventScroll: true });
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    status.textContent = error.name === 'TimeoutError' ? 'Сервер отвечает слишком долго. Попробуй ещё раз.' : error instanceof TypeError ? 'Не удалось связаться с сервером. Проверь соединение и повтори.' : error.message;
  } finally {
    oracleLoading.hidden = true;
    status.classList.remove('is-pending');
    submit.removeAttribute('aria-busy');
    submit.disabled = false;
  }
});
document.querySelector('#again').addEventListener('click', () => {
  document.querySelector('#full-name').focus({ preventScroll: true });
  form.scrollIntoView({ behavior: 'smooth', block: 'start' });
});
loadQuestions();
