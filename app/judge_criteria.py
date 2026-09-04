"""Scoring criteria for the LLM-as-judge feature (see app/judge.py).

These are the anchors that tell the model what a 1 vs. a 3 vs. a 5 looks
like. They're plain code, not user-editable through the UI - the judge is
meant to read like an independent reviewer applying a fixed bar, not the
proposal writer grading their own work.

Two levels; the more specific one wins:

- RFP_CRITERIA: keyed by ``(rfp_template_id, rfp_section_id)``, both taken
  from an RFP template JSON (app/rfp/<template>.json) - the template's
  top-level "id" and one of its "sections[].id". Custom sections created via
  Import RFP (app/rfp.py) carry that tag forward automatically, so writing
  a criteria entry here once tunes scoring for every proposal built from
  that RFP - useful for funders/programs you apply to repeatedly.
- SECTION_CRITERIA: generic fallback, keyed by section type - "scope",
  "qualifications", or "custom" (any custom section with no RFP-specific
  entry above). Used whenever nothing more specific applies.

Edit these directly; restart the app to pick up changes.
"""

SECTION_CRITERIA = {
    "scope": (
        "1 = Vague or missing; no clear activities, timeline, or measurable outcomes.\n"
        "3 = Activities are named but outcomes are generic; unclear how success is measured.\n"
        "5 = Specific, sequenced activities tied to clear, measurable outcomes and a realistic timeline."
    ),
    "qualifications": (
        "1 = Generic claims of experience with no specific examples or evidence.\n"
        "3 = Some relevant experience cited, but not clearly tied to this project's needs.\n"
        "5 = Directly relevant past work, named team members' expertise, and clear evidence of "
        "capacity to deliver this specific project."
    ),
    "custom": (
        "1 = Does not address the section's purpose or any stated requirement.\n"
        "3 = Partially addresses the purpose; some required points are missing or thin.\n"
        "5 = Fully and specifically addresses the section's purpose and every stated requirement."
    ),
}

# Populate as you tune criteria for a specific, repeatedly-used RFP. Example:
#
# RFP_CRITERIA = {
#     ("cal-fire-wpb-2025", "cal-fire-wpb-2025-bg"): (
#         "1 = No mention of the applicant's wood products experience.\n"
#         "3 = General forestry experience cited but not wood-products-specific.\n"
#         "5 = Specific past wood products projects named, with named staff and outcomes."
#     ),
# }
RFP_CRITERIA: dict[tuple[str, str], str] = {}


def get_criteria(section_key: str, rfp_source: tuple[str, str] | None) -> str:
    """Return the criteria text for a section, most specific match first."""
    if rfp_source and rfp_source in RFP_CRITERIA:
        return RFP_CRITERIA[rfp_source]
    return SECTION_CRITERIA.get(section_key, SECTION_CRITERIA["custom"])
