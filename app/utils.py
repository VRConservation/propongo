"""Utility functions for Propongo."""

from typing import Dict, Any


def build_export_context(proposal) -> Dict[str, Any]:
    """Build context dictionary for export and preview templates.
    
    Args:
        proposal: Proposal object
        
    Returns:
        dict: Context dictionary with all necessary template variables
    """
    indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
    indirect_amount = proposal.total_budget * (indirect_percent / 100)
    total_with_indirect = proposal.total_budget + indirect_amount

    tasks_with_timing = []
    for t in proposal.tasks:
        tasks_with_timing.append({
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "description": t.get("description", ""),
            "lead_entity": t.get("lead_entity", ""),
            "start_month": t.get("start_month"),
            "start_year": t.get("start_year"),
            "duration_months": t.get("duration_months", 1),
            "recurring": t.get("recurring", False),
            "recurring_interval": t.get("recurring_interval", 3),
        })

    budget_with_timing = []
    timings = proposal.budget_item_timings or {}
    for item in proposal.budget_items:
        item_id = item.get("id", "")
        timing = timings.get(item_id, {})
        budget_with_timing.append({
            **item,
            "start_month": timing.get("start_month"),
            "start_year": timing.get("start_year"),
            "duration_months": timing.get("duration_months", 1),
            "task_id": item.get("task_id", ""),
            "recurring": timing.get("recurring", False),
            "recurring_interval": timing.get("recurring_interval", 3),
        })

    from datetime import datetime as _dt
    try:
        sd = _dt.strptime(proposal.start_date, "%Y-%m-%d")
        proj_start_month = sd.month
        proj_start_year = sd.year
    except (ValueError, TypeError):
        proj_start_month = 1
        proj_start_year = 2025

    try:
        ed = _dt.strptime(proposal.end_date, "%Y-%m-%d") if proposal.end_date else None
        proj_end_month = ed.month if ed else proj_start_month
        proj_end_year = ed.year if ed else proj_start_year + 1
    except (ValueError, TypeError):
        proj_end_month = proj_start_month
        proj_end_year = proj_start_year + 1

    if proposal.end_date:
        timeline_total_months = max((proj_end_year - proj_start_year) * 12 + (proj_end_month - proj_start_month) + 1, 1)
    else:
        max_end = 0
        for t in tasks_with_timing:
            sm = t.get("start_month") or proj_start_month
            sy = t.get("start_year") or proj_start_year
            offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
            dur = t.get("duration_months") or 1
            if t.get("recurring"):
                interval = t.get("recurring_interval") or 3
                last = offset
                while last < 120:
                    end = last + dur
                    if end > max_end:
                        max_end = end
                    last += interval
            else:
                end = offset + dur
                if end > max_end:
                    max_end = end
        for bi in budget_with_timing:
            sm = bi.get("start_month") or proj_start_month
            sy = bi.get("start_year") or proj_start_year
            offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
            dur = bi.get("duration_months") or 1
            if bi.get("recurring"):
                interval = bi.get("recurring_interval") or 3
                last = offset
                while last < 120:
                    end = last + dur
                    if end > max_end:
                        max_end = end
                    last += interval
            else:
                end = offset + dur
                if end > max_end:
                    max_end = end
        timeline_total_months = max(max_end, 1)
    if timeline_total_months <= 12:
        timeline_granularity = "months"
    elif timeline_total_months <= 36:
        timeline_granularity = "quarters"
    else:
        timeline_granularity = "years"

    task_bi_data = {}
    for bi in budget_with_timing:
        tid = bi.get("task_id", "")
        if not tid:
            continue
        sm = bi.get("start_month") or proj_start_month
        sy = bi.get("start_year") or proj_start_year
        bi_offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
        bi_dur = bi.get("duration_months") or 1
        if tid not in task_bi_data:
            task_bi_data[tid] = {"min_offset": bi_offset, "max_end": bi_offset + bi_dur}
        else:
            task_bi_data[tid]["min_offset"] = min(task_bi_data[tid]["min_offset"], bi_offset)
            task_bi_data[tid]["max_end"] = max(task_bi_data[tid]["max_end"], bi_offset + bi_dur)

    all_rows = []
    for t in tasks_with_timing:
        sm = t.get("start_month") or proj_start_month
        sy = t.get("start_year") or proj_start_year
        offset = (sy - proj_start_year) * 12 + (sm - proj_start_month)
        dur = t.get("duration_months") or 1
        tid = t.get("id", "")
        recurring = t.get("recurring", False)
        interval = t.get("recurring_interval") or 3

        if tid in task_bi_data:
            offset = task_bi_data[tid]["min_offset"]
            dur = task_bi_data[tid]["max_end"] - task_bi_data[tid]["min_offset"]
            if dur < 1:
                dur = 1
            recurring = False

        if recurring:
            bars = []
            r_offset = offset
            while r_offset < timeline_total_months:
                bars.append({"offset": r_offset, "duration": dur})
                r_offset += interval
            all_rows.append({
                "name": t.get("name", ""),
                "bars": bars,
                "is_indent": False,
                "lead_entity": t.get("lead_entity", ""),
            })
        else:
            all_rows.append({
                "name": t.get("name", ""),
                "bars": [{"offset": offset, "duration": dur}],
                "is_indent": False,
                "lead_entity": t.get("lead_entity", ""),
            })

        for bi in budget_with_timing:
            if bi.get("task_id") == tid:
                bi_sm = bi.get("start_month") or sm
                bi_sy = bi.get("start_year") or sy
                bi_offset = (bi_sy - proj_start_year) * 12 + (bi_sm - proj_start_month)
                bi_dur = bi.get("duration_months") or 1
                bi_recurring = bi.get("recurring", False)
                bi_interval = bi.get("recurring_interval") or 3
                if bi_recurring:
                    bars = []
                    br_offset = bi_offset
                    while br_offset < timeline_total_months:
                        bars.append({"offset": br_offset, "duration": bi_dur})
                        br_offset += bi_interval
                    all_rows.append({
                        "name": bi.get("name", ""),
                        "bars": bars,
                        "is_indent": True,
                        "lead_entity": "",
                    })
                else:
                    all_rows.append({
                        "name": bi.get("name", ""),
                        "bars": [{"offset": bi_offset, "duration": bi_dur}],
                        "is_indent": True,
                        "lead_entity": "",
                    })

    return {
        "proposal": proposal,
        "tasks": tasks_with_timing,
        "budget_items": proposal.budget_items,
        "budget_with_timing": budget_with_timing,
        "total_budget": proposal.total_budget,
        "indirect_percent": indirect_percent,
        "indirect_amount": indirect_amount,
        "total_with_indirect": total_with_indirect,
        "timeline_granularity": timeline_granularity,
        "timeline_total_months": timeline_total_months,
        "all_rows": all_rows,
        "budget_by_year": build_budget_by_year(proposal),
    }


def build_budget_by_year(proposal) -> Dict[str, Any]:
    """Allocate budget items across calendar years based on their spend dates.

    Each item's cost is spread evenly over the months of its user-defined
    spend window (``budget_item_timings``). Items with no dates set are
    reported as unscheduled so totals still reconcile.
    """
    timings = getattr(proposal, "budget_item_timings", None) or {}
    by_year = {}
    unscheduled = []

    for item in proposal.budget_items:
        total = float(item.get("cost_per_unit", 0) * item.get("units", 0))
        if total <= 0:
            continue
        timing = timings.get(item.get("id", ""), {})
        sm = timing.get("start_month")
        sy = timing.get("start_year")
        dur = timing.get("duration_months")
        if not (sm and sy and dur):
            unscheduled.append({"name": item.get("name", ""), "amount": total})
            continue

        start = int(sy) * 12 + (int(sm) - 1)
        dur = max(int(dur), 1)
        monthly = total / dur
        for m in range(dur):
            y = (start + m) // 12
            by_year[y] = by_year.get(y, 0.0) + monthly

    years = [{"year": y, "amount": round(by_year[y], 2)} for y in sorted(by_year)]
    return {
        "years": years,
        "unscheduled": unscheduled,
        "total_scheduled": round(sum(r["amount"] for r in years), 2),
        "total_unscheduled": round(sum(u["amount"] for u in unscheduled), 2),
    }


def build_tracker_export_context(proposal) -> Dict[str, Any]:
    """Build context dictionary for tracker export templates.

    Args:
        proposal: Proposal object

    Returns:
        dict: Context dictionary with all necessary template variables
    """
    indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
    indirect_amount = proposal.total_budget * (indirect_percent / 100)
    total_with_indirect = proposal.total_budget + indirect_amount

    timings = proposal.budget_item_timings or {}
    task_budgets = {}
    for task in proposal.tasks:
        items = [b for b in proposal.budget_items if b.get("task_id") == task["id"]]
        for item in items:
            t = timings.get(item.get("id", ""), {})
            if t:
                item["actual_cost"] = t.get("actual_cost", 0)
        subtotal = sum(i.get("cost_per_unit", 0) * i.get("units", 0) for i in items)
        actual_total = sum(i.get("actual_cost", 0) for i in items)
        task_budgets[task["id"]] = {
            "task": task,
            "items": items,
            "subtotal": subtotal,
            "actual_total": actual_total,
        }

    total_actual = sum(tb["actual_total"] for tb in task_budgets.values())

    milestones = getattr(proposal, 'milestones', []) or []
    reports = getattr(proposal, 'reports', []) or []

    completed_tasks = sum(1 for t in proposal.tasks if t.get("status") == "completed")
    total_tasks = len(proposal.tasks)
    overall_pct = round(completed_tasks / total_tasks * 100) if total_tasks else 0

    return {
        "proposal": proposal,
        "tasks": proposal.tasks,
        "task_budgets": task_budgets,
        "total_budget": proposal.total_budget,
        "indirect_percent": indirect_percent,
        "indirect_amount": indirect_amount,
        "total_with_indirect": total_with_indirect,
        "total_actual": total_actual,
        "milestones": milestones,
        "reports": reports,
        "overall_pct": overall_pct,
    }
