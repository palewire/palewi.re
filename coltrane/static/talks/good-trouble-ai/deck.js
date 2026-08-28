import Reveal from "/static/talks/reveal/reveal.esm.js";

const slides = document.querySelector("#slides");
for (let number = 1; number <= 30; number += 1) {
  const section = document.createElement("section");
  const image = document.createElement("img");
  image.src = `slides/slide-${String(number).padStart(2, "0")}.png`;
  image.alt = `Slide ${number} of 30`;
  section.append(image);
  slides.append(section);
}
new Reveal({
  controls: true,
  embedded: true,
  hash: true,
  height: 1125,
  margin: 0,
  progress: true,
  width: 2000,
}).initialize();
