import enum
from enum import StrEnum

from ninja import Schema
from pydantic import EmailStr
from pydantic import SecretStr


class TimezoneChoices(StrEnum):
    AFRICA_ABIDJAN = "Africa/Abidjan"
    AFRICA_ACCRA = "Africa/Accra"
    AFRICA_ADDIS_ABABA = "Africa/Addis_Ababa"
    AFRICA_ALGIERS = "Africa/Algiers"
    AFRICA_ASMARA = "Africa/Asmara"
    AFRICA_ASMERA = "Africa/Asmera"
    AFRICA_BAMAKO = "Africa/Bamako"
    AFRICA_BANGUI = "Africa/Bangui"
    AFRICA_BANJUL = "Africa/Banjul"
    AFRICA_BISSAU = "Africa/Bissau"
    AFRICA_BLANTYRE = "Africa/Blantyre"
    AFRICA_BRAZZAVILLE = "Africa/Brazzaville"
    AFRICA_BUJUMBURA = "Africa/Bujumbura"
    AFRICA_CAIRO = "Africa/Cairo"
    AFRICA_CASABLANCA = "Africa/Casablanca"
    AFRICA_CEUTA = "Africa/Ceuta"
    AFRICA_CONAKRY = "Africa/Conakry"
    AFRICA_DAKAR = "Africa/Dakar"
    AFRICA_DAR_ES_SALAAM = "Africa/Dar_es_Salaam"
    AFRICA_DJIBOUTI = "Africa/Djibouti"
    AFRICA_DOUALA = "Africa/Douala"
    AFRICA_EL_AAIUN = "Africa/El_Aaiun"
    AFRICA_FREETOWN = "Africa/Freetown"
    AFRICA_GABORONE = "Africa/Gaborone"
    AFRICA_HARARE = "Africa/Harare"
    AFRICA_JOHANNESBURG = "Africa/Johannesburg"
    AFRICA_JUBA = "Africa/Juba"
    AFRICA_KAMPALA = "Africa/Kampala"
    AFRICA_KHARTOUM = "Africa/Khartoum"
    AFRICA_KIGALI = "Africa/Kigali"
    AFRICA_KINSHASA = "Africa/Kinshasa"
    AFRICA_LAGOS = "Africa/Lagos"
    AFRICA_LIBREVILLE = "Africa/Libreville"
    AFRICA_LOME = "Africa/Lome"
    AFRICA_LUANDA = "Africa/Luanda"
    AFRICA_LUBUMBASHI = "Africa/Lubumbashi"
    AFRICA_LUSAKA = "Africa/Lusaka"
    AFRICA_MALABO = "Africa/Malabo"
    AFRICA_MAPUTO = "Africa/Maputo"
    AFRICA_MASERU = "Africa/Maseru"
    AFRICA_MBABANE = "Africa/Mbabane"
    AFRICA_MOGADISHU = "Africa/Mogadishu"
    AFRICA_MONROVIA = "Africa/Monrovia"
    AFRICA_NAIROBI = "Africa/Nairobi"
    AFRICA_NDJAMENA = "Africa/Ndjamena"
    AFRICA_NIAMEY = "Africa/Niamey"
    AFRICA_NOUAKCHOTT = "Africa/Nouakchott"
    AFRICA_OUAGADOUGOU = "Africa/Ouagadougou"
    AFRICA_PORTO_NOVO = "Africa/Porto-Novo"
    AFRICA_SAO_TOME = "Africa/Sao_Tome"
    AFRICA_TIMBUKTU = "Africa/Timbuktu"
    AFRICA_TRIPOLI = "Africa/Tripoli"
    AFRICA_TUNIS = "Africa/Tunis"
    AFRICA_WINDHOEK = "Africa/Windhoek"
    AMERICA_ADAK = "America/Adak"
    AMERICA_ANCHORAGE = "America/Anchorage"
    AMERICA_ANGUILLA = "America/Anguilla"
    AMERICA_ANTIGUA = "America/Antigua"
    AMERICA_ARAGUAINA = "America/Araguaina"
    AMERICA_ARGENTINA_BUENOS_AIRES = "America/Argentina/Buenos_Aires"
    AMERICA_ARGENTINA_CATAMARCA = "America/Argentina/Catamarca"
    AMERICA_ARGENTINA_COMODRIVADAVIA = "America/Argentina/ComodRivadavia"
    AMERICA_ARGENTINA_CORDOBA = "America/Argentina/Cordoba"
    AMERICA_ARGENTINA_JUJUY = "America/Argentina/Jujuy"
    AMERICA_ARGENTINA_LA_RIOJA = "America/Argentina/La_Rioja"
    AMERICA_ARGENTINA_MENDOZA = "America/Argentina/Mendoza"
    AMERICA_ARGENTINA_RIO_GALLEGOS = "America/Argentina/Rio_Gallegos"
    AMERICA_ARGENTINA_SALTA = "America/Argentina/Salta"
    AMERICA_ARGENTINA_SAN_JUAN = "America/Argentina/San_Juan"
    AMERICA_ARGENTINA_SAN_LUIS = "America/Argentina/San_Luis"
    AMERICA_ARGENTINA_TUCUMAN = "America/Argentina/Tucuman"
    AMERICA_ARGENTINA_USHUAIA = "America/Argentina/Ushuaia"
    AMERICA_ARUBA = "America/Aruba"
    AMERICA_ASUNCION = "America/Asuncion"
    AMERICA_ATIKOKAN = "America/Atikokan"
    AMERICA_ATKA = "America/Atka"
    AMERICA_BAHIA = "America/Bahia"
    AMERICA_BAHIA_BANDERAS = "America/Bahia_Banderas"
    AMERICA_BARBADOS = "America/Barbados"
    AMERICA_BELEM = "America/Belem"
    AMERICA_BELIZE = "America/Belize"
    AMERICA_BLANC_SABLON = "America/Blanc-Sablon"
    AMERICA_BOA_VISTA = "America/Boa_Vista"
    AMERICA_BOGOTA = "America/Bogota"
    AMERICA_BOISE = "America/Boise"
    AMERICA_BUENOS_AIRES = "America/Buenos_Aires"
    AMERICA_CAMBRIDGE_BAY = "America/Cambridge_Bay"
    AMERICA_CAMPO_GRANDE = "America/Campo_Grande"
    AMERICA_CANCUN = "America/Cancun"
    AMERICA_CARACAS = "America/Caracas"
    AMERICA_CATAMARCA = "America/Catamarca"
    AMERICA_CAYENNE = "America/Cayenne"
    AMERICA_CAYMAN = "America/Cayman"
    AMERICA_CHICAGO = "America/Chicago"
    AMERICA_CHIHUAHUA = "America/Chihuahua"
    AMERICA_CIUDAD_JUAREZ = "America/Ciudad_Juarez"
    AMERICA_CORAL_HARBOUR = "America/Coral_Harbour"
    AMERICA_CORDOBA = "America/Cordoba"
    AMERICA_COSTA_RICA = "America/Costa_Rica"
    AMERICA_COYHAIQUE = "America/Coyhaique"
    AMERICA_CRESTON = "America/Creston"
    AMERICA_CUIABA = "America/Cuiaba"
    AMERICA_CURACAO = "America/Curacao"
    AMERICA_DANMARKSHAVN = "America/Danmarkshavn"
    AMERICA_DAWSON = "America/Dawson"
    AMERICA_DAWSON_CREEK = "America/Dawson_Creek"
    AMERICA_DENVER = "America/Denver"
    AMERICA_DETROIT = "America/Detroit"
    AMERICA_DOMINICA = "America/Dominica"
    AMERICA_EDMONTON = "America/Edmonton"
    AMERICA_EIRUNEPE = "America/Eirunepe"
    AMERICA_EL_SALVADOR = "America/El_Salvador"
    AMERICA_ENSENADA = "America/Ensenada"
    AMERICA_FORT_NELSON = "America/Fort_Nelson"
    AMERICA_FORT_WAYNE = "America/Fort_Wayne"
    AMERICA_FORTALEZA = "America/Fortaleza"
    AMERICA_GLACE_BAY = "America/Glace_Bay"
    AMERICA_GODTHAB = "America/Godthab"
    AMERICA_GOOSE_BAY = "America/Goose_Bay"
    AMERICA_GRAND_TURK = "America/Grand_Turk"
    AMERICA_GRENADA = "America/Grenada"
    AMERICA_GUADELOUPE = "America/Guadeloupe"
    AMERICA_GUATEMALA = "America/Guatemala"
    AMERICA_GUAYAQUIL = "America/Guayaquil"
    AMERICA_GUYANA = "America/Guyana"
    AMERICA_HALIFAX = "America/Halifax"
    AMERICA_HAVANA = "America/Havana"
    AMERICA_HERMOSILLO = "America/Hermosillo"
    AMERICA_INDIANA_INDIANAPOLIS = "America/Indiana/Indianapolis"
    AMERICA_INDIANA_KNOX = "America/Indiana/Knox"
    AMERICA_INDIANA_MARENGO = "America/Indiana/Marengo"
    AMERICA_INDIANA_PETERSBURG = "America/Indiana/Petersburg"
    AMERICA_INDIANA_TELL_CITY = "America/Indiana/Tell_City"
    AMERICA_INDIANA_VEVAY = "America/Indiana/Vevay"
    AMERICA_INDIANA_VINCENNES = "America/Indiana/Vincennes"
    AMERICA_INDIANA_WINAMAC = "America/Indiana/Winamac"
    AMERICA_INDIANAPOLIS = "America/Indianapolis"
    AMERICA_INUVIK = "America/Inuvik"
    AMERICA_IQALUIT = "America/Iqaluit"
    AMERICA_JAMAICA = "America/Jamaica"
    AMERICA_JUJUY = "America/Jujuy"
    AMERICA_JUNEAU = "America/Juneau"
    AMERICA_KENTUCKY_LOUISVILLE = "America/Kentucky/Louisville"
    AMERICA_KENTUCKY_MONTICELLO = "America/Kentucky/Monticello"
    AMERICA_KNOX_IN = "America/Knox_IN"
    AMERICA_KRALENDIJK = "America/Kralendijk"
    AMERICA_LA_PAZ = "America/La_Paz"
    AMERICA_LIMA = "America/Lima"
    AMERICA_LOS_ANGELES = "America/Los_Angeles"
    AMERICA_LOUISVILLE = "America/Louisville"
    AMERICA_LOWER_PRINCES = "America/Lower_Princes"
    AMERICA_MACEIO = "America/Maceio"
    AMERICA_MANAGUA = "America/Managua"
    AMERICA_MANAUS = "America/Manaus"
    AMERICA_MARIGOT = "America/Marigot"
    AMERICA_MARTINIQUE = "America/Martinique"
    AMERICA_MATAMOROS = "America/Matamoros"
    AMERICA_MAZATLAN = "America/Mazatlan"
    AMERICA_MENDOZA = "America/Mendoza"
    AMERICA_MENOMINEE = "America/Menominee"
    AMERICA_MERIDA = "America/Merida"
    AMERICA_METLAKATLA = "America/Metlakatla"
    AMERICA_MEXICO_CITY = "America/Mexico_City"
    AMERICA_MIQUELON = "America/Miquelon"
    AMERICA_MONCTON = "America/Moncton"
    AMERICA_MONTERREY = "America/Monterrey"
    AMERICA_MONTEVIDEO = "America/Montevideo"
    AMERICA_MONTREAL = "America/Montreal"
    AMERICA_MONTSERRAT = "America/Montserrat"
    AMERICA_NASSAU = "America/Nassau"
    AMERICA_NEW_YORK = "America/New_York"
    AMERICA_NIPIGON = "America/Nipigon"
    AMERICA_NOME = "America/Nome"
    AMERICA_NORONHA = "America/Noronha"
    AMERICA_NORTH_DAKOTA_BEULAH = "America/North_Dakota/Beulah"
    AMERICA_NORTH_DAKOTA_CENTER = "America/North_Dakota/Center"
    AMERICA_NORTH_DAKOTA_NEW_SALEM = "America/North_Dakota/New_Salem"
    AMERICA_NUUK = "America/Nuuk"
    AMERICA_OJINAGA = "America/Ojinaga"
    AMERICA_PANAMA = "America/Panama"
    AMERICA_PANGNIRTUNG = "America/Pangnirtung"
    AMERICA_PARAMARIBO = "America/Paramaribo"
    AMERICA_PHOENIX = "America/Phoenix"
    AMERICA_PORT_AU_PRINCE = "America/Port-au-Prince"
    AMERICA_PORT_OF_SPAIN = "America/Port_of_Spain"
    AMERICA_PORTO_ACRE = "America/Porto_Acre"
    AMERICA_PORTO_VELHO = "America/Porto_Velho"
    AMERICA_PUERTO_RICO = "America/Puerto_Rico"
    AMERICA_PUNTA_ARENAS = "America/Punta_Arenas"
    AMERICA_RAINY_RIVER = "America/Rainy_River"
    AMERICA_RANKIN_INLET = "America/Rankin_Inlet"
    AMERICA_RECIFE = "America/Recife"
    AMERICA_REGINA = "America/Regina"
    AMERICA_RESOLUTE = "America/Resolute"
    AMERICA_RIO_BRANCO = "America/Rio_Branco"
    AMERICA_ROSARIO = "America/Rosario"
    AMERICA_SANTA_ISABEL = "America/Santa_Isabel"
    AMERICA_SANTAREM = "America/Santarem"
    AMERICA_SANTIAGO = "America/Santiago"
    AMERICA_SANTO_DOMINGO = "America/Santo_Domingo"
    AMERICA_SAO_PAULO = "America/Sao_Paulo"
    AMERICA_SCORESBYSUND = "America/Scoresbysund"
    AMERICA_SHIPROCK = "America/Shiprock"
    AMERICA_SITKA = "America/Sitka"
    AMERICA_ST_BARTHELEMY = "America/St_Barthelemy"
    AMERICA_ST_JOHNS = "America/St_Johns"
    AMERICA_ST_KITTS = "America/St_Kitts"
    AMERICA_ST_LUCIA = "America/St_Lucia"
    AMERICA_ST_THOMAS = "America/St_Thomas"
    AMERICA_ST_VINCENT = "America/St_Vincent"
    AMERICA_SWIFT_CURRENT = "America/Swift_Current"
    AMERICA_TEGUCIGALPA = "America/Tegucigalpa"
    AMERICA_THULE = "America/Thule"
    AMERICA_THUNDER_BAY = "America/Thunder_Bay"
    AMERICA_TIJUANA = "America/Tijuana"
    AMERICA_TORONTO = "America/Toronto"
    AMERICA_TORTOLA = "America/Tortola"
    AMERICA_VANCOUVER = "America/Vancouver"
    AMERICA_VIRGIN = "America/Virgin"
    AMERICA_WHITEHORSE = "America/Whitehorse"
    AMERICA_WINNIPEG = "America/Winnipeg"
    AMERICA_YAKUTAT = "America/Yakutat"
    AMERICA_YELLOWKNIFE = "America/Yellowknife"
    ANTARCTICA_CASEY = "Antarctica/Casey"
    ANTARCTICA_DAVIS = "Antarctica/Davis"
    ANTARCTICA_DUMONTDURVILLE = "Antarctica/DumontDUrville"
    ANTARCTICA_MACQUARIE = "Antarctica/Macquarie"
    ANTARCTICA_MAWSON = "Antarctica/Mawson"
    ANTARCTICA_MCMURDO = "Antarctica/McMurdo"
    ANTARCTICA_PALMER = "Antarctica/Palmer"
    ANTARCTICA_ROTHERA = "Antarctica/Rothera"
    ANTARCTICA_SOUTH_POLE = "Antarctica/South_Pole"
    ANTARCTICA_SYOWA = "Antarctica/Syowa"
    ANTARCTICA_TROLL = "Antarctica/Troll"
    ANTARCTICA_VOSTOK = "Antarctica/Vostok"
    ARCTIC_LONGYEARBYEN = "Arctic/Longyearbyen"


class ImagesPerPageChoices(int, enum.Enum):
    TEN = 10
    TWENTY = 20
    THIRTY = 30
    FORTY = 40
    FIFTY = 50
    SIXTY = 60
    SEVENTY = 70
    EIGHTY = 80
    NINETY = 90
    ONE_HUNDRED = 100


class UserInCreateSchema(Schema):
    first_name: str
    last_name: str
    username: str
    password: SecretStr
    email: EmailStr | None = None
    is_staff: bool = False
    is_superuser: bool = False


class UserOutSchema(UserInCreateSchema):
    id: int
    email: EmailStr | str | None = None


class UserUpdateInScheme(UserInCreateSchema):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    # TODO: Password change functionality


class UserProfileUpdateSchema(Schema):
    items_per_page: ImagesPerPageChoices | None = None
    bio: str | None | None = None
    timezone: TimezoneChoices | None = None


class UserProfileOutSchema(Schema):
    items_per_page: ImagesPerPageChoices = ImagesPerPageChoices.THIRTY
    bio: str | None
    timezone: TimezoneChoices


class GroupInCreateSchema(Schema):
    name: str


class GroupOut(GroupInCreateSchema):
    id: int


class GroupAssignSchema(Schema):
    id: int
