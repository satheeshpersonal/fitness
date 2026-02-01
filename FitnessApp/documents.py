from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from models import Gym, GymMedia, GymEquipment, GymReview

gym_index = Index('gyms')
gym_index.settings(number_of_shards=1, number_of_replicas=0)

@registry.register_document
class GymDocument(Document):
    media = fields.ObjectField(properties={
        'media': fields.TextField(),
        'description': fields.TextField()
    })
    equipment = fields.ObjectField(properties={
        'category': fields.TextField(),
        'description': fields.TextField()
    })
    average_rating = fields.FloatField()
    city = fields.TextField()
    # latitude = fields.FloatField()
    # longitude = fields.FloatField()
    location = fields.GeoPointField()

    class Index:
        name = 'gyms'

    class Django:
        model = Gym
        fields = [
            'name', 'description', 'city', 'state', 'country', 'address', 'premium_type'
        ]

    def prepare_media(self, instance):
        return [{'media': m.media.url, 'description': m.description} for m in instance.gymmedia_set.all()]

    def prepare_equipment(self, instance):
        return [{'category': e.category, 'description': e.description} for e in instance.gymequipment_set.all()]

    def prepare_average_rating(self, instance):
        reviews = instance.gymreview_set.all()
        if not reviews.exists():
            return 0.0
        return sum([r.rating for r in reviews]) / reviews.count()
    
    def prepare_location(self, instance):
        return {
            "lat": instance.latitude,
            "lon": instance.longitude
        }
