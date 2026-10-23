"""Concatenate per-root member CSV bodies into one file with a single header."""

from docorder.functions.reduce_function import ReduceFunction

HEADER = "root_id|member_id|member_zh|definition|is_default|scope_filter|time_basis|attribution|aliases"


class CombineRootMember(ReduceFunction):
    def transform_data(self, sources, target):
        rows: list[str] = []
        for source in sorted(sources, key=lambda item: item.name):
            for line in source.read_text().splitlines():
                stripped = line.strip()
                if not stripped or stripped == HEADER:
                    continue
                rows.append(stripped)
        body = HEADER + "\n"
        if rows:
            body += "\n".join(rows) + "\n"
        target.staging_data = body

    def transform_props(self, sources, target):
        target.tag = {"roots": len(sources)}
