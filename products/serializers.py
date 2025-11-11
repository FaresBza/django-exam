from rest_framework import serializers
from .models import Product, Review
from django.db.models import Avg


class ProductSerializer(serializers.ModelSerializer):
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    """
        Représentation d'un produit vendable.
        - name: nom commercial
        - price: prix TTC en euros (doit être > 0)
        - created_at: horodatage de création (lecture seule)
        """

    class Meta:
        model = Product
        fields = ("id", "name", "price", "created_at", "avg_rating", "reviews_count")
        read_only_fields = ("created_at", "avg_rating", "reviews_count")

    def get_avg_rating(self, obj):
        if hasattr(obj, "avg_rating") and obj.avg_rating is not None:
            return round(float(obj.avg_rating), 2)
        agg = obj.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(float(agg) if agg is not None else 0.0, 2)

    def get_reviews_count(self, obj):
        if hasattr(obj, "reviews_count") and obj.reviews_count is not None:
            return obj.reviews_count
        return obj.reviews.count()


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # affiche le username

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("user", "created_at")

        def validate_rating(self, value):
            if value < 1 or value > 5:
                raise serializers.ValidationError("La note doit être entre 1 et 5.")
            return value

        def validate(self, attrs):
            # empêcher un 2e avis sur le même produit par le même user à lacréation
            request = self.context.get("request")
            if request and request.method == "POST":
                product = attrs.get("product")
                if product and Review.objects.filter(product=product, user=request.user).exists():
                    raise serializers.ValidationError("Vous avez déjà laissé un avis pour ce produit.")
