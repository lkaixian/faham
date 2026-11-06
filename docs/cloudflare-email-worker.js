// Cloudflare Email Worker: hands every email sent to faham@yourdomain to FAHAM, which replies to the sender.
// Worker settings (Settings > Variables and Secrets):
//   FAHAM_URL    text    https://faham.yourdomain.com          (no trailing slash)
//   FAHAM_SECRET secret  the same value as EMAIL_WEBHOOK_SECRET in FAHAM's .env
export default {
  // Visiting the worker URL in a browser lands here. Email never uses this; it only avoids Cloudflare error 1101.
  async fetch() {
    return new Response("FAHAM email worker is running. It only handles email.");
  },

  async email(message, env, ctx) {
    if (message.rawSize > 25 * 1024 * 1024) { message.setReject("Message too large"); return; }
    const raw = await new Response(message.raw).arrayBuffer();
    const r = await fetch(env.FAHAM_URL + "/api/channels/email?reply=1", {
      method: "POST",
      headers: { "x-faham-secret": env.FAHAM_SECRET, "content-type": "message/rfc822" },
      body: raw,
    });
    if (!r.ok) message.setReject("FAHAM is not available right now. Please try again later.");
  },
};
