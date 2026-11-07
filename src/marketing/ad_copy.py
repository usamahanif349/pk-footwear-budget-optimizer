"""
Ad copy and campaign brief generator.

Turns the budget plan (where to spend), the audience view (who to target) and the
Project 1 review aspects (what to say) into ready-to-use ad copy per platform, in
English and Roman Urdu. Template based: no paid AI service, so it always works.

The copy is SAMPLE copy written by this tool for a class project. It is not the
brands' real advertising and uses none of their real slogans.
"""

# ---------------- MESSAGE ANGLES (from Project 1 aspects) ----------------
# Each angle has a headline (short enough for a Google search ad: 30 chars) and a
# line of body text, in English (en) and Roman Urdu (ru).
ANGLES = {
    "comfort": dict(
        en=("Comfort that lasts all day", "Soft cushioning made for long days on your feet."),
        ru=("Saara din aaram", "Naram cushioning, lambe din ke liye bana.")),
    "design": dict(
        en=("Styles that turn heads", "Fresh designs and colours for every outfit."),
        ru=("Har outfit ka naya style", "Naye designs, naye rang, har mauqe ke liye.")),
    "quality": dict(
        en=("Built to last", "Quality materials and stitching you can see."),
        ru=("Mazboot aur pakke joote", "Achha material, pakki silai, lambi chalne wali.")),
    "price": dict(
        en=("Great shoes, fair price", "Quality footwear that respects your budget."),
        ru=("Achhe joote, sahi qeemat", "Budget mein behtareen joote.")),
    "size": dict(
        en=("Your perfect fit, guaranteed", "Check our size guide. Wrong size? Exchange it easily."),
        ru=("Sahi size, pakki guarantee", "Size guide dekhein. Size ghalat ho to aasaan exchange.")),
    "staff": dict(
        en=("Shop online, skip the queue", "Order from home and get it delivered fast."),
        ru=("Ghar baithe order karein", "Online order karein, jaldi delivery paayein.")),
    "delivery": dict(
        en=("Delivered to your door", "Fast, tracked delivery across Pakistan."),
        ru=("Ghar tak delivery", "Poore Pakistan mein tez delivery.")),
}
# A short reassurance line that answers a complaint without making it the headline.
FIX_LINE = {
    "price": dict(en="Prices shown upfront, with bundle deals.",
                  ru="Qeemat saaf likhi hai, bundle deals ke saath."),
    "quality": dict(en="Every pair checked before it ships.",
                    ru="Har joota bhejne se pehle check hota hai."),
    "size": dict(en="Easy size exchange, no questions asked.",
                 ru="Size exchange bilkul aasaan."),
    "staff": dict(en="Prefer to skip the store? Order online.",
                  ru="Store nahin jaana? Online order karein."),
    "delivery": dict(en="Delivery times you can count on.",
                     ru="Delivery waqt par."),
    "comfort": dict(en="Comfort tested for all-day wear.",
                    ru="Saare din ke liye aaram test kiya gaya."),
    "design": dict(en="New designs added every season.",
                   ru="Har season naye designs."),
}

# ---------------- CAMPAIGN HOOKS ----------------
CAMPAIGNS = {
    "Always-On Brand": dict(en="New season, new steps.", ru="Naye season ke naye qadam.",
                            tag="#NewCollection", short="New Collection", kw="new collection"),
    "Eid ul Fitr Sale": dict(en="Step into Eid in style.", ru="Eid ki tayari, naye jooton ke saath.",
                             tag="#EidCollection", short="Eid Collection", kw="eid shoes"),
    "Eid ul Adha Sale": dict(en="Eid ul Adha ready? Your shoes are.", ru="Bari Eid par naya andaz.",
                             tag="#EidUlAdha", short="Eid Collection", kw="eid shoes"),
    "Back to School": dict(en="Back to school, ready to walk.", ru="School wapas, qadam mazboot.",
                           tag="#BackToSchool", short="School Shoes", kw="school shoes"),
    "Winter Collection": dict(en="The winter collection is here.",
                              ru="Sardiyon ki nayi collection aa gayi.", tag="#WinterCollection",
                              short="Winter Collection", kw="winter shoes"),
    "11.11 Mega Sale": dict(en="The 11.11 Mega Sale is live.", ru="11.11 Mega Sale shuru!",
                            tag="#1111Sale", short="11.11 Sale", kw="11.11 sale"),
}

# ---------------- PLATFORM FORMATS ----------------
PLATFORMS = {
    "TikTok": dict(
        format="Vertical video (9:16), 15–30 s",
        tips="Show the shoe in the first 2 seconds, use a trending sound, film it creator-style "
             "(try-on, unboxing, outfit check) rather than as a polished ad.",
        cta=dict(en="Shop now", ru="Abhi order karein")),
    "Instagram": dict(
        format="Reel (9:16) + Story, or a 3–5 image carousel",
        tips="Lead with the best-looking shot, put the price or offer on the first frame, "
             "add a 'Shop' sticker to Stories.",
        cta=dict(en="Shop now", ru="Abhi order karein")),
    "Facebook": dict(
        format="Carousel or single image in the feed",
        tips="Show 3–5 styles with prices, and turn on Messenger replies: many buyers ask "
             "questions before ordering.",
        cta=dict(en="Shop now", ru="Abhi order karein")),
    "Google": dict(
        format="Responsive search ad (headlines ≤ 30 characters, descriptions ≤ 90)",
        tips="Target people already searching: brand name + 'shoes', 'sale', 'Eid'. Send them "
             "straight to the matching product page.",
        cta=dict(en="Order online", ru="Online order karein")),
    "YouTube": dict(
        format="6 s bumper or 15 s skippable video",
        tips="Show the brand and product in the first 5 seconds, before the Skip button appears.",
        cta=dict(en="Shop now", ru="Abhi order karein")),
}

GOOGLE_HEADLINE_MAX, GOOGLE_DESC_MAX = 30, 90


def _tag(text):
    return "#" + "".join(ch for ch in text.title() if ch.isalnum())


def angles_for(praise, fixes):
    """Pick a lead angle (A) and a test angle (B), plus a reassurance line.
    praise / fixes: lists of aspect names, strongest first."""
    lead = praise[0] if praise else (fixes[0] if fixes else "design")
    candidates = list(praise[1:]) + [f for f in fixes if f != lead] + ["design", "comfort"]
    test = next(a for a in candidates if a != lead)
    fix = next((f for f in fixes if f not in (lead, test)), None)
    return lead, test, fix


def ad_copy(brand, platform, campaign, lead, test, fix, lang="en"):
    """Copy for one platform and campaign, with an A/B pair of headlines."""
    hook = CAMPAIGNS[campaign][lang]
    head_a, body_a = ANGLES[lead][lang]
    head_b, body_b = ANGLES[test][lang]
    cta = PLATFORMS[platform]["cta"][lang]
    fix_line = f" {FIX_LINE[fix][lang]}" if fix else ""
    hashtags = " ".join([_tag(brand), _tag(brand + " shoes"), CAMPAIGNS[campaign]["tag"],
                         "#PakistaniFashion"])
    out = dict(headline_a=head_a, headline_b=head_b,
               text_a=f"{hook} {body_a}{fix_line} {cta}.",
               text_b=f"{hook} {body_b}{fix_line} {cta}.",
               cta=cta, hashtags=hashtags)
    if platform == "Google":
        heads = [f"{brand} Shoes", head_a, head_b, f"{brand} {CAMPAIGNS[campaign]['short']}"]
        heads = [h for h in heads if len(h) <= GOOGLE_HEADLINE_MAX]
        descs = [f"{body_a}{fix_line}".strip(), f"{body_b} {cta} today.".strip()]
        descs = [d if len(d) <= GOOGLE_DESC_MAX else d[:GOOGLE_DESC_MAX - 1] + "…" for d in descs]
        out.update(google_headlines=heads, google_descriptions=descs,
                   keywords=[f"{brand.lower()} shoes", f"{brand.lower()} sale",
                             f"{brand.lower()} {CAMPAIGNS[campaign]['kw']}",
                             "shoes online pakistan"])
    return out


def brief_text(brand, campaign, budget, plan_rows, copies, audiences, lead, test, fix):
    """Plain-text campaign brief: everything a designer and media buyer need."""
    lines = [f"CAMPAIGN BRIEF: {brand} | {campaign}",
             "Sample copy generated by the budget optimizer (class project). Ad data simulated;",
             "messaging based on real customer reviews (Project 1).", "",
             f"Monthly budget: Rs. {budget:,.0f}",
             f"Lead message: {lead} | Test message: {test}"
             + (f" | Reassure on: {fix}" if fix else ""), ""]
    for p, share, spend in plan_rows:
        c = copies[p]
        lines += [f"=== {p}: {share:.1f}% (Rs. {spend:,.0f}) ===",
                  f"Format: {PLATFORMS[p]['format']}",
                  f"Audience: {audiences.get(p, '-')}",
                  f"Tips: {PLATFORMS[p]['tips']}"]
        for lang, label in (("en", "English"), ("ru", "Roman Urdu")):
            x = c[lang]
            lines += [f"[{label}] Headline A: {x['headline_a']}",
                      f"[{label}] Headline B: {x['headline_b']}",
                      f"[{label}] Text A: {x['text_a']}",
                      f"[{label}] Text B: {x['text_b']}"]
            if "google_headlines" in x:
                lines += [f"[{label}] Search headlines: " + " | ".join(x["google_headlines"]),
                          f"[{label}] Search descriptions: " + " | ".join(x["google_descriptions"])]
        lines += [f"Hashtags: {c['en']['hashtags']}", ""]
    lines += ["A/B TEST: run Headline A and Headline B with equal budget for the first week,",
              "then move the budget to whichever gets more orders per rupee."]
    return "\n".join(lines)
