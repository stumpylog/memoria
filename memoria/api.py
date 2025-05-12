from ninja import NinjaAPI

from memoria.common.parser import OrjsonParser
from memoria.common.renderer import OrjsonRenderer
from memoria.routes.albums.api import router as albums_router
from memoria.routes.authentication.api import router as auth_router
from memoria.routes.images.api import router as images_router
from memoria.routes.locations.api import router as locations_router
from memoria.routes.people.api import router as person_router
from memoria.routes.pets.api import router as pets_router
from memoria.routes.rough_dates.api import router as rough_dates_router
from memoria.routes.tags.api import router as tags_router
from memoria.routes.users.api import router as user_router

api = NinjaAPI(title="Memoria API", renderer=OrjsonRenderer(), parser=OrjsonParser(), csrf=True)
api.add_router("/person/", person_router)
api.add_router("/tag/", tags_router)
api.add_router("/image/", images_router)
api.add_router("/album/", albums_router)
api.add_router("/pet/", pets_router)
api.add_router("/location/", locations_router)
api.add_router("/date/", rough_dates_router)
api.add_router("/auth/", auth_router)
api.add_router("/user/", user_router)
