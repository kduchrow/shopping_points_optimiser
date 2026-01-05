from abc import ABC, abstractmethod
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spo.extensions import db
from spo.models import Shop, ShopProgramRate, utcnow
from spo.services.bonus_programs import ensure_program
from spo.services.dedup import get_or_create_shop_main


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self):
        """Return shop data dict:
        {
          'name': 'ShopName',
          'rates': [
            {'program': 'Payback', 'points_per_eur': 1.0, 'cashback_pct': 0.0, 'point_value_eur': 0.005},
          ]
        }
        """

    def register_to_db(self, data):
        """Register shop and rates to database using ShopMain + ShopVariant deduplication"""
        
        # Get or create ShopMain with automatic deduplication
        shop_main, is_new, confidence = get_or_create_shop_main(
            shop_name=data['name'],
            source=self.__class__.__name__,
            source_id=data.get('source_id')
        )
        
        # For backward compatibility, update legacy Shop table
        shop = Shop.query.filter_by(name=data['name']).first()
        if not shop:
            shop = Shop(name=data['name'], shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()
        else:
            if not shop.shop_main_id:
                shop.shop_main_id = shop_main.id
                db.session.commit()

        now = utcnow()
        
        for r in data.get('rates', []):
            prog = ensure_program(r['program'], point_value_eur=r.get('point_value_eur', 0.0))
            
            # Get currently active rate (no valid_to set)
            existing = ShopProgramRate.query.filter_by(
                shop_id=shop.id, 
                program_id=prog.id,
                valid_to=None
            ).first()
            
            new_points = r.get('points_per_eur', 0.0)
            new_cashback = r.get('cashback_pct', 0.0)
            
            if not existing:
                # No previous rate, create new one
                new_rate = ShopProgramRate(
                    shop_id=shop.id,
                    program_id=prog.id,
                    points_per_eur=new_points,
                    cashback_pct=new_cashback,
                    valid_from=now,
                    valid_to=None,
                )
                db.session.add(new_rate)
            else:
                # Check if values changed
                if existing.points_per_eur != new_points or existing.cashback_pct != new_cashback:
                    # Archive old rate
                    existing.valid_to = now
                    db.session.merge(existing)
                    
                    # Create new rate
                    new_rate = ShopProgramRate(
                        shop_id=shop.id,
                        program_id=prog.id,
                        points_per_eur=new_points,
                        cashback_pct=new_cashback,
                        valid_from=now,
                        valid_to=None,
                    )
                    db.session.add(new_rate)

        db.session.commit()
