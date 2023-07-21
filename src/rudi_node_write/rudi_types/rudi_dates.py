from builtins import staticmethod

from rudi_node_write.rudi_types.serializable import Serializable
from rudi_node_write.utils.date_utils import now_iso
from rudi_node_write.utils.dict_utils import check_is_dict
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.type_date import Date


class RudiDates(Serializable):
    def __init__(
        self,
        created: str = None,
        updated: str = None,
        validated: str = None,
        published: str = None,
        expires: str = None,
        deleted: str = None,
    ):
        self.created = Date.from_str(created, now_iso())
        self.updated = Date.from_str(updated, now_iso())
        if self.created > self.updated:
            upd = self.updated
            self.updated = self.created
            self.created = upd
        self.validated = Date.from_str(validated)
        self.published = Date.from_str(published)
        self.expires = Date.from_str(expires)
        self.deleted = Date.from_str(deleted)

    @staticmethod
    def from_json(o: dict | None):
        if o is None:
            return RudiDates()
        check_is_dict(o)
        return RudiDates(
            created=o.get("created"),
            updated=o.get("updated"),
            validated=o.get("validated"),
            published=o.get("published"),
            expires=o.get("expires"),
            deleted=o.get("deleted"),
        )


if __name__ == "__main__":  # pragma: no cover
    tests = "RudiDates tests"
    log_d(tests, "empty", RudiDates())
    default_rudi_dates = RudiDates(updated="2023-02-10T14:32:06+02:00")
    log_d(tests, "created", default_rudi_dates.created)
    log_d(tests, "is validated None", default_rudi_dates.validated is None)
    log_d(tests, "default_rudi_dates", default_rudi_dates)
    log_d(tests, "default_rudi_dates.to_json()", default_rudi_dates.to_json())
    log_d(
        tests,
        "RudiDates.deserialize",
        RudiDates.from_json(default_rudi_dates.to_json()),
    )
