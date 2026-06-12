from .start import router as start_router
from .subscription import router as subscription_router
from .pdf_tools import router as pdf_router
from .admin import router as admin_router

routers = [start_router, subscription_router, pdf_router, admin_router]
