from news_grouper.api import create_app
from news_grouper.api.config import ProdConfig

app = create_app(ProdConfig)
