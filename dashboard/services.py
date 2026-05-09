from booking.services import BookingAnalytic
from screening.services import ScreeningAnalytic


class DashboardService:
    @staticmethod
    def get_full_manager_report():
        """ Retrieve data from multiple domains into a single dashboard view for managers. """
        # 1. Fetch data from the existing specialized services
        financials = BookingAnalytic.financial_report()
        bookings = BookingAnalytic.booking_report()
        top_movies = ScreeningAnalytic.top_movies()
        occupancy = ScreeningAnalytic.showtime_occupancy()

        # 2. Return the combined "Big Picture"
        return {
            "summary": {
                "recent_bookings": bookings[:10], # Limit to top 10 for dashboard clarity
                "top_movies": top_movies[:5] if top_movies else None,
            },
            "financial_breakdown": financials,
            "upcoming_schedule": occupancy
        }

