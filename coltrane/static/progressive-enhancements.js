function loadSoundCloudEmbeds() {
  document.querySelectorAll("[data-soundcloud-embed]").forEach((embed) => {
    const controls = embed.querySelector(".soundcloud-embed__controls");
    const button = controls?.querySelector("button");
    const status = controls?.querySelector(".soundcloud-embed__status");
    const template = embed.querySelector("template");

    if (!controls || !button || !status || !template) {
      return;
    }

    controls.classList.add("is-ready");
    button.addEventListener("click", () => {
      const iframe = template.content.firstElementChild?.cloneNode(true);
      if (!(iframe instanceof HTMLIFrameElement)) {
        return;
      }

      let loaded = false;
      button.disabled = true;
      status.textContent = "Loading the SoundCloud player.";
      iframe.classList.add("soundcloud-embed__player");
      iframe.addEventListener("load", () => {
        if (loaded) {
          return;
        }
        loaded = true;
        window.clearTimeout(timeout);
        iframe.focus();
        controls.hidden = true;
      });
      const timeout = window.setTimeout(() => {
        if (loaded) {
          return;
        }
        loaded = true;
        iframe.remove();
        button.disabled = false;
        status.textContent = "The player could not load. Open it in SoundCloud instead.";
      }, 10000);
      embed.append(iframe);
    });
  });
}

loadSoundCloudEmbeds();
