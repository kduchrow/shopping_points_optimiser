"""
Test script for shop deduplication system
"""

from app import app, db
from shop_dedup import get_or_create_shop_main, fuzzy_match_score
from models import ShopMain, ShopVariant

def test_shop_dedup():
    with app.app_context():
        print("\n=== Shop Deduplication Test ===\n")
        
        # Test 1: Create first shop
        print("1. Creating 'Amazon' from Miles & More...")
        shop1, created1, conf1 = get_or_create_shop_main("Amazon", "miles_and_more", "12345")
        print(f"   Result: {'NEW' if created1 else 'EXISTING'} (confidence: {conf1}%)")
        print(f"   ShopMain ID: {shop1.id}")
        
        # Test 2: Try to create same shop with different case
        print("\n2. Creating 'AMAZON' from Payback...")
        shop2, created2, conf2 = get_or_create_shop_main("AMAZON", "payback", "67890")
        print(f"   Result: {'NEW' if created2 else 'EXISTING'} (confidence: {conf2}%)")
        print(f"   ShopMain ID: {shop2.id}")
        print(f"   Same shop? {shop1.id == shop2.id}")
        
        # Test 3: Create similar but not identical shop
        print("\n3. Creating 'Amazone' from manual entry...")
        shop3, created3, conf3 = get_or_create_shop_main("Amazone", "manual", None)
        print(f"   Result: {'NEW' if created3 else 'EXISTING'} (confidence: {conf3}%)")
        print(f"   ShopMain ID: {shop3.id}")
        print(f"   Same as Amazon? {shop1.id == shop3.id}")
        print(f"   ⚠️ Needs review: {conf3 < 98}")
        
        # Test 4: Create completely different shop
        print("\n4. Creating 'Zalando' from Payback...")
        shop4, created4, conf4 = get_or_create_shop_main("Zalando", "payback", "11111")
        print(f"   Result: {'NEW' if created4 else 'EXISTING'} (confidence: {conf4}%)")
        print(f"   ShopMain ID: {shop4.id}")
        
        # Show all shops and variants
        print("\n=== Database State ===\n")
        print(f"ShopMain entries: {ShopMain.query.count()}")
        print(f"ShopVariant entries: {ShopVariant.query.count()}")
        
        print("\nShopMain Details:")
        for sm in ShopMain.query.all():
            print(f"  {sm.canonical_name} (ID: {sm.id[:8]}...)")
            variants = ShopVariant.query.filter_by(shop_main_id=sm.id).all()
            for v in variants:
                print(f"    - {v.source}: '{v.source_name}' (confidence: {v.confidence_score}%)")
        
        # Test similarity scores
        print("\n=== Similarity Scores ===")
        test_pairs = [
            ("Amazon", "AMAZON"),
            ("Amazon", "amazon"),
            ("Amazon", "Amazone"),
            ("Amazon", "amz"),
            ("Zalando", "Amazon"),
        ]
        for s1, s2 in test_pairs:
            score = fuzzy_match_score(s1, s2)
            print(f"  '{s1}' vs '{s2}': {score}%")
        
        print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_shop_dedup()
