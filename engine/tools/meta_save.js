// Save Meta AI images by name. Runs inside the meta.ai tab (Claude in Chrome: javascript_tool).
// Paste this whole file once per tab, then:
//   metaSave.init('sm4')             marks every image already on the page as seen; prefix = this run's tag.
//                                    Call it again after any page reload (a reload lazy-loads old images).
//   await metaSave.wait()            after sending a prompt: waits until a new image arrives and the page
//                                    stops changing (max 60 s). Returns "ready 1 new" or "timeout ...".
//   await metaSave.save('s_vault')   downloads the oldest unseen image as sm4_s_vault.<real type> into
//                                    ~/Downloads; then move it to the run's incoming/ and run match_images.py.
//                                    Two prompts in one batch: save them in the order they were sent.
//                                    It says how many new images are left; one left after the last save
//                                    usually means Meta sent a second version: look before saving it.
// Why: agents' one-off helpers saved lazy-loaded OLD images and guessed the file type (one PNG came back as .webp).
// Safety: only an image lower on the page than every image already seen counts as new (answers stack downwards).
(() => {
  const big = () => [...document.querySelectorAll('img')]
    .filter((i) => i.src.startsWith('https://') && Math.max(i.naturalWidth, i.naturalHeight) >= 800);
  const top = (i) => i.getBoundingClientRect().top + window.scrollY;
  const key = (i) => i.src.split('?')[0];
  const EXT = { 'image/webp': 'webp', 'image/png': 'png', 'image/jpeg': 'jpg' };

  window.metaSave = {
    prefix: null, seen: new Set(), lowest: -Infinity, log: [],
    init(prefix) {
      if (!/^[a-z0-9]{2,8}$/.test(prefix)) return 'prefix must be 2-8 chars a-z/0-9';
      this.prefix = prefix;
      for (const i of big()) { this.seen.add(key(i)); this.lowest = Math.max(this.lowest, top(i)); }
      return `ready: ${this.seen.size} old image(s) marked as seen`;
    },
    fresh() {
      return big().filter((i) => !this.seen.has(key(i)) && top(i) > this.lowest)
        .sort((a, b) => top(a) - top(b));
    },
    async wait(maxMs = 60000) {
      const t0 = Date.now(); let last = '', since = Date.now();
      while (Date.now() - t0 < maxMs) {
        const sig = this.fresh().length + '|' + document.body.innerText.length;
        if (sig !== last) { last = sig; since = Date.now(); }
        if (this.fresh().length > 0 && Date.now() - since > 4000) return `ready ${this.fresh().length} new`;
        await new Promise((r) => setTimeout(r, 500));
      }
      return `timeout (${this.fresh().length} new)`;
    },
    async save(name) {
      if (!this.prefix) return 'call metaSave.init(prefix) first';
      if (!/^[A-Za-z0-9_-]{2,60}$/.test(name)) return 'bad name';
      const f = this.fresh();
      if (f.length === 0) return 'NO NEW IMAGE (not saved): wait longer or re-send the prompt';
      const img = f[0]; // the highest new one = the oldest unsaved answer
      const blob = await (await fetch(img.src)).blob();
      const ext = EXT[blob.type];
      if (!ext) return `not an image (${blob.type}), not saved`;
      const file = `${this.prefix}_${name}.${ext}`;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = file;
      document.body.appendChild(a); a.click(); a.remove();
      this.seen.add(key(img));
      this.lowest = Math.max(this.lowest, top(img));
      this.log.push(file);
      return `saved ${file} ${img.naturalWidth}x${img.naturalHeight}, ${f.length - 1} new image(s) left`;
    },
  };
  return 'metaSave loaded';
})();
