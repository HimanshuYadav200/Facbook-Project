// Save Meta AI images by name. Runs inside the meta.ai tab (Claude in Chrome: javascript_tool).
// Paste this whole file once per tab, then:
//   metaSave.init('luc')             prefix = this run's tag (2-8 chars). Marks the images already on the page as seen.
//   send ONE prompt, then:
//   await metaSave.wait(35000)       waits until a new image is the last one on the page and the page stops changing.
//                                    Returns "ready" or "timeout": on timeout just call it again (the browser tool
//                                    stops any call after 45 s, so keep each wait under 40 s).
//   await metaSave.save('s_vault')   downloads that image as luc_s_vault.<real type> into ~/Downloads; then move it to
//                                    the run's incoming/ and run match_images.py.
// Rule: the newest answer is always the LAST big image on the page, so save() takes the last image and refuses
// if it was already saved. Why not "any unseen image": meta.ai unloads older images as the chat grows and reloads
// them under new addresses, so old images look new (2026-11-11: 2 "new" images, only 1 was); save() also compares
// the image bytes with earlier saves. One prompt at a time; one prompt per browser batch (longer batches time out).
// A refusal ("protected character") gives no image: wait() times out and save() refuses; reword and re-send.
(() => {
  const big = () => [...document.querySelectorAll('img')]
    .filter((i) => i.src.startsWith('https://') && Math.max(i.naturalWidth, i.naturalHeight) >= 800);
  const key = (i) => i.src.split('?')[0];
  const EXT = { 'image/webp': 'webp', 'image/png': 'png', 'image/jpeg': 'jpg' };

  window.metaSave = {
    prefix: null, seen: new Set(), hashes: new Set(), log: [],
    init(prefix) {
      if (!/^[a-z0-9]{2,8}$/.test(prefix)) return 'prefix must be 2-8 chars a-z/0-9';
      this.prefix = prefix;
      for (const i of big()) this.seen.add(key(i));
      return `ready: ${this.seen.size} old image(s) marked as seen`;
    },
    newest() {
      const all = big();
      const last = all[all.length - 1];
      return last && !this.seen.has(key(last)) ? last : null;
    },
    async wait(maxMs = 35000) {
      const t0 = Date.now(); let sig = '', since = Date.now();
      while (Date.now() - t0 < maxMs) {
        const n = this.newest();
        const s = (n ? key(n) : '-') + '|' + document.body.innerText.length;
        if (s !== sig) { sig = s; since = Date.now(); }
        if (n && Date.now() - since > 4000) return 'ready';
        await new Promise((r) => setTimeout(r, 500));
      }
      return 'timeout';
    },
    async save(name) {
      if (!this.prefix) return 'call metaSave.init(prefix) first';
      if (!/^[A-Za-z0-9_-]{2,60}$/.test(name)) return 'bad name';
      const img = this.newest();
      if (!img) return 'NO NEW IMAGE (not saved): wait longer or re-send the prompt';
      const blob = await (await fetch(img.src)).blob();
      const ext = EXT[blob.type];
      if (!ext) return `not an image (${blob.type}), not saved`;
      // same picture under a new address (reloaded old image): compare the bytes, not the address
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-1', await blob.arrayBuffer()))].join(',');
      if (this.hashes.has(hash)) { this.seen.add(key(img)); return 'SAME IMAGE AS AN EARLIER SAVE (not saved): wait longer or re-send the prompt'; }
      const file = `${this.prefix}_${name}.${ext}`;
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = file;
      document.body.appendChild(a); a.click(); a.remove();
      this.seen.add(key(img)); this.hashes.add(hash);
      this.log.push(file);
      return `saved ${file} ${img.naturalWidth}x${img.naturalHeight}`;
    },
  };
  return 'metaSave loaded';
})();
