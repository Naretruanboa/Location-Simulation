export function setupJoystick(send, allowed) {
  const pad = document.querySelector("#joystick"),
    stick = document.querySelector("#stick");
  const keys = new Set();
  let active = false,
    bearing = 0,
    pointer = null;
  const stop = () => {
    keys.clear();
    pointer = null;
    if (active) send({ type: "movement", active: false });
    active = false;
    stick.style.transform = "";
  };
  const move = (x, y) => {
    if (!allowed()) {
      stop();
      return;
    }
    const magnitude = Math.hypot(x, y);
    if (magnitude < 0.12) {
      if (active) send({ type: "movement", active: false });
      active = false;
      stick.style.transform = "";
      return;
    }
    bearing = ((Math.atan2(x, -y) * 180) / Math.PI + 360) % 360;
    active = true;
    stick.style.transform = `translate(${(x / Math.max(1, magnitude)) * 38}px,${(y / Math.max(1, magnitude)) * 38}px)`;
    send({ type: "movement", active: true, bearing });
  };
  const point = (e) => {
    const box = pad.getBoundingClientRect();
    move(
      (e.clientX - box.left - box.width / 2) / 45,
      (e.clientY - box.top - box.height / 2) / 45,
    );
  };
  pad.onpointerdown = (e) => {
    if (!allowed()) return;
    e.preventDefault();
    pad.setPointerCapture(e.pointerId);
    pointer = e.pointerId;
    point(e);
  };
  pad.onpointermove = (e) => {
    if (pointer === e.pointerId) point(e);
  };
  pad.onpointerup = pad.onpointercancel = pad.onlostpointercapture = stop;
  const directions = {
    w: [0, -1],
    arrowup: [0, -1],
    s: [0, 1],
    arrowdown: [0, 1],
    a: [-1, 0],
    arrowleft: [-1, 0],
    d: [1, 0],
    arrowright: [1, 0],
  };
  function keyboard(e, pressed) {
    const key = e.key.toLowerCase();
    if (!directions[key]) return;
    if (
      pressed &&
      (e.target.closest('input,textarea,select,[contenteditable="true"]') ||
        e.metaKey ||
        e.ctrlKey ||
        e.altKey)
    )
      return;
    e.preventDefault();
    if (pressed) keys.add(key);
    else keys.delete(key);
    let x = 0,
      y = 0;
    for (const k of keys) {
      x += directions[k][0];
      y += directions[k][1];
    }
    if (x || y) move(x, y);
    else stop();
  }
  window.addEventListener("keydown", (e) => keyboard(e, true));
  window.addEventListener("keyup", (e) => keyboard(e, false));
  window.addEventListener("blur", stop);
  window.addEventListener("pagehide", stop);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
  });
  setInterval(() => {
    if (active) {
      if (allowed()) send({ type: "movement", active: true, bearing });
      else stop();
    }
  }, 200);
  return stop;
}
