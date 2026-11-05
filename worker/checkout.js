// llamaxy.com checkout (Apo 4 Nov 2026): basket → Stripe Checkout session. Prices and stock come from
// llamaxy.com/prices.json (built hourly from our FBA stock), never from the browser; max 3 per product.
// Secrets: STRIPE_TEST, STRIPE_LIVE. Live payments when var LIVE = "1" (on since Apo 5 Nov 2026).
const SITE = 'https://llamaxy.com/'
const H = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type', 'Content-Type': 'application/json' }
const out = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: H })

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: H })
    if (req.method !== 'POST') return out({ error: 'POST only' }, 405)
    const { items, test, base, email } = await req.json().catch(() => ({}))
    const key = test ? env.STRIPE_TEST : env.LIVE === '1' && env.STRIPE_LIVE
    if (!key) return out({ error: 'Our payment service is temporarily unavailable. You have not been charged.' }, 503)
    const back = typeof base === 'string' && base.startsWith(SITE) ? base : SITE
    if (!Array.isArray(items) || !items.length || items.length > 12) return out({ error: 'Your basket can hold up to 12 different items.' }, 400)
    const prices = await (await fetch(SITE + 'prices.json', { cf: { cacheTtl: 60 } })).json()
    const lines = []
    for (const x of items) {
      const p = prices[x.a], q = Number(x.q)
      if (!p) return out({ error: 'Sorry, an item in your basket has just sold out. Please remove it and try again.' }, 409)
      if (!Number.isInteger(q) || q < 1 || q > 3) return out({ error: 'Maximum 3 of each item per order.' }, 400)
      lines.push({ a: x.a, q, p: p.p, t: p.t, i: p.i })
    }
    // Max 3 of each item per customer over 30 days (Apo 5 Nov 2026), by the email given before payment;
    // the order loop on our server checks the delivery address as well
    const mail = typeof email === 'string' ? email.trim().toLowerCase() : ''
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) return out({ error: 'Please enter a valid email address.' }, 400)
    const since = Math.floor(Date.now() / 1000) - 30 * 86400
    const prev = await (await fetch(`https://api.stripe.com/v1/checkout/sessions?status=complete&limit=100&created[gte]=${since}&customer_details[email]=${encodeURIComponent(mail)}`, { headers: { Authorization: 'Bearer ' + key } })).json()
    const had = {}
    for (const s of prev.data ?? []) if (s.payment_status === 'paid') for (const x of JSON.parse(s.metadata?.items || '[]')) had[x.a] = (had[x.a] ?? 0) + x.q
    for (const x of lines) if ((had[x.a] ?? 0) + x.q > 3)
      return out({ error: `You can buy up to 3 of each item${had[x.a] ? ` — you have already ordered ${had[x.a]} of “${x.t.slice(0, 60)}” recently` : ''}. Want more? Please contact us at info@llamaxy.com.` }, 409)
    const sub = lines.reduce((n, x) => n + x.p * x.q, 0)
    const f = {
      mode: 'payment', locale: 'en-GB', customer_email: mail, 'adaptive_pricing[enabled]': 'false', // always GBP (4 Nov: OVH FR IP showed EUR +4% fee)
      success_url: back + 'thanks.html', cancel_url: back + 'basket.html',
      'shipping_address_collection[allowed_countries][0]': 'GB',
      'phone_number_collection[enabled]': 'true',
      'shipping_options[0][shipping_rate_data][display_name]': 'Standard UK delivery (1–2 working days to dispatch)',
      'shipping_options[0][shipping_rate_data][type]': 'fixed_amount',
      'shipping_options[0][shipping_rate_data][fixed_amount][amount]': String(sub >= 40 ? 0 : 399),
      'shipping_options[0][shipping_rate_data][fixed_amount][currency]': 'gbp',
      'metadata[items]': JSON.stringify(lines.map(({ a, q, p }) => ({ a, q, p }))),
    }
    lines.forEach((x, i) => {
      f[`line_items[${i}][quantity]`] = String(x.q)
      f[`line_items[${i}][price_data][currency]`] = 'gbp'
      f[`line_items[${i}][price_data][unit_amount]`] = String(Math.round(x.p * 100))
      f[`line_items[${i}][price_data][product_data][name]`] = x.t
      if (x.i) f[`line_items[${i}][price_data][product_data][images][0]`] = SITE + x.i
    })
    const r = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST', body: new URLSearchParams(f),
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    const j = await r.json()
    if (!r.ok) return out({ error: 'Payment could not be started. You have not been charged — please try again.' }, 502)
    return out({ url: j.url })
  },
}
