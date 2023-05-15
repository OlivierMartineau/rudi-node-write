from rudi_node_write.utils.date import nowISO, ensure_date_str
from rudi_node_write.utils.log import log_d
from rudi_node_write.utils.serializable import Serializable
from rudi_node_write.utils.type_dict import check_is_dict


class RudiDates(Serializable):
    def __init__(self, created: str = None, updated: str = None, validated: str = None, published: str = None,
                 expires: str = None, deleted: str = None):
        self.created = ensure_date_str(created, ensure_date_str(updated, nowISO()))
        self.updated = ensure_date_str(updated, self.created)
        if self.created > self.updated:
            self.created = self.updated
        self.validated = ensure_date_str(validated)
        self.published = ensure_date_str(published)
        self.expires = ensure_date_str(expires)
        self.deleted = ensure_date_str(deleted)

    @staticmethod
    def from_dict(o: dict):
        if o is None:
            return RudiDates()
        check_is_dict(o)
        updated = o.get('updated')
        created_iso = ensure_date_str(o.get('created'), ensure_date_str(updated, nowISO()))
        updated_iso = ensure_date_str(updated, created_iso)
        if created_iso > updated_iso:
            created_iso = updated_iso
        validated_iso = ensure_date_str(o.get('validated'), None, True)
        published_iso = ensure_date_str(o.get('published'), None, True)
        expires_iso = ensure_date_str(o.get('expires'), None, True)
        deleted_iso = ensure_date_str(o.get('deleted'), None, True)
        return RudiDates(created=created_iso, updated=updated_iso, validated=validated_iso, published=published_iso,
                         expires=expires_iso, deleted=deleted_iso)


if __name__ == '__main__':
    fun = 'RudiDates tests'
    log_d(fun, 'empty', RudiDates())
    default_rudi_dates = RudiDates(updated='2023-02-10T14:32:06+02:00')
    log_d(fun, 'created', default_rudi_dates.created)
    log_d(fun, 'is validated None', default_rudi_dates.validated is None)
    log_d(fun, 'default_rudi_dates', default_rudi_dates)
    log_d(fun, 'RudiDates.from_json', RudiDates.from_dict(default_rudi_dates.to_json_dict()))
