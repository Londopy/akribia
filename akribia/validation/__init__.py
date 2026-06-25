"""Validation suite (spec 2.6) — what separates a toy model from a rigorous one.

Two load-bearing facts the field already knows are planned for here, not
discovered mid-build: HGF parameter recovery is genuinely hard, and matching a
reference toolbox bit-for-bit is weeks of work. So we (a) treat an existing
validated HGF as the reference oracle rather than chasing bit-exactness, and
(b) report recovery PER PARAMETER and expect some parameters not to recover.
"""
