(function () {
  "use strict";

  const CX = 150, CY = 150;
  const R_OUTER = 138, R_MINOR_IN = 120, R_MAJOR_IN = 113, R_NUM = 100;

  const dialFace = document.getElementById("dialFace");
  const pwInput = document.getElementById("pw");
  const toggleVis = document.getElementById("toggleVis");
  const scoreNumber = document.getElementById("scoreNumber");
  const dialLabel = document.getElementById("dialLabel");
  const entropyValue = document.getElementById("entropyValue");
  const criteriaList = document.getElementById("criteriaList");
  const warningsBlock = document.getElementById("warnings");
  const warningsList = document.getElementById("warningsList");
  const suggestionsList = document.getElementById("suggestionsList");

  const svgns = "http://www.w3.org/2000/svg";

  function polar(cx, cy, r, deg) {
    const rad = ((deg - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  }

  // Build the 0-100 tick ring once.
  function buildDial() {
    for (let i = 0; i <= 100; i += 5) {
      const deg = (i / 100) * 360;
      const isMajor = i % 20 === 0;
      const inner = isMajor ? R_MAJOR_IN : R_MINOR_IN;
      const p1 = polar(CX, CY, R_OUTER - 4, deg);
      const p2 = polar(CX, CY, inner, deg);

      const line = document.createElementNS(svgns, "line");
      line.setAttribute("x1", p1.x.toFixed(2));
      line.setAttribute("y1", p1.y.toFixed(2));
      line.setAttribute("x2", p2.x.toFixed(2));
      line.setAttribute("y2", p2.y.toFixed(2));
      line.setAttribute("class", "tickmark" + (isMajor ? " major" : ""));
      dialFace.appendChild(line);

      if (isMajor) {
        const p3 = polar(CX, CY, R_NUM, deg);
        const text = document.createElementNS(svgns, "text");
        text.setAttribute("x", p3.x.toFixed(2));
        text.setAttribute("y", (p3.y + 4).toFixed(2));
        text.setAttribute("class", "tick-num");
        text.textContent = i;
        dialFace.appendChild(text);
      }
    }
  }

  function setDialRotation(score) {
    const deg = (score / 100) * 360;
    dialFace.style.transform = `rotate(${deg}deg)`;
  }

  function labelState(label) {
    return label.toLowerCase();
  }

  function render(data) {
    scoreNumber.textContent = data.score;
    setDialRotation(data.score);

    dialLabel.textContent = data.label;
    dialLabel.dataset.state = labelState(data.label);

    entropyValue.textContent = data.entropy.toFixed ? data.entropy.toFixed(1) : data.entropy;

    // Criteria
    criteriaList.querySelectorAll("li").forEach((li) => {
      const key = li.dataset.key;
      li.classList.toggle("met", !!data.criteria[key]);
    });

    // Warnings
    if (data.warnings && data.warnings.length) {
      warningsBlock.hidden = false;
      warningsList.innerHTML = "";
      data.warnings.forEach((w) => {
        const li = document.createElement("li");
        li.textContent = w;
        warningsList.appendChild(li);
      });
    } else {
      warningsBlock.hidden = true;
    }

    // Suggestions
    suggestionsList.innerHTML = "";
    (data.suggestions || []).forEach((s) => {
      const li = document.createElement("li");
      li.textContent = s;
      suggestionsList.appendChild(li);
    });
  }

  let debounceTimer = null;
  function checkPassword() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const password = pwInput.value;
      try {
        const res = await fetch("/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password }),
        });
        const data = await res.json();
        render(data);
      } catch (err) {
        console.error("Password check failed:", err);
      }
    }, 120);
  }

  toggleVis.addEventListener("click", () => {
    const showing = pwInput.type === "text";
    pwInput.type = showing ? "password" : "text";
    toggleVis.textContent = showing ? "show" : "hide";
    toggleVis.setAttribute("aria-label", showing ? "Show password" : "Hide password");
  });

  pwInput.addEventListener("input", checkPassword);

  buildDial();
  checkPassword(); // render the empty state
})();
