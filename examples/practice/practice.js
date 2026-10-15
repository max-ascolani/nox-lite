"use strict";
// This fixture never reads file bytes, persists inputs, or sends a network request.
const form = document.querySelector("#application");
const scenario = document.querySelector("#scenario");
const result = document.querySelector("#result");
const submit = document.querySelector("#submit");
const travel = document.querySelector("#travel");
const question = document.querySelector("#new-question");
const cv = document.querySelector("#cv");
const fileStatus = document.querySelector("#file-status");
const initialFileMessage = fileStatus.textContent;

function clearOutcome() {
  result.hidden = true;
  result.textContent = "";
  delete result.dataset.outcome;
  question.hidden = true;
  travel.required = false;
  travel.value = "";
  submit.disabled = false;
}

function show(outcome, message) {
  result.hidden = false;
  result.dataset.outcome = outcome;
  result.textContent = message;
}

scenario.addEventListener("change", clearOutcome);
document.querySelector("#reset").addEventListener("click", () => {
  form.reset();
  scenario.value = "success";
  fileStatus.textContent = initialFileMessage;
  clearOutcome();
});
cv.addEventListener("change", () => {
  fileStatus.textContent = cv.files.length ? "Selected locally: " + cv.files[0].name + ". No file contents read or uploaded." : initialFileMessage;
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (scenario.value === "validation") {
    show("failed", "Mock validation error: the fictional employer rejected this file format. No mock application was accepted. Inspect the error and correct it before another attempt.");
  } else if (scenario.value === "uncertain") {
    show("unconfirmed", "Mock connection interrupted after the final action. No receipt is available. Outcome: unconfirmed. Check existing evidence before any retry.");
    submit.disabled = true;
  } else if (scenario.value === "question" && question.hidden) {
    question.hidden = false;
    travel.required = true;
    show("decision_needed", "New required question appeared. No mock receipt. The candidate must decide about overnight travel before continuing.");
  } else {
    show("confirmed", "MOCK RECEIPT — PRACTICE ONLY\nExample Studio · Operations Coordinator · Vacancy #42\nReference: NOX-PRACTICE-42\nThe local practice flow is complete. Nothing was sent to an employer.");
    submit.disabled = true;
  }
});
