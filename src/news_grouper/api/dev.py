import sqlalchemy as sa
import sqlalchemy.orm as so

from news_grouper.api import create_app
from news_grouper.api.config import DevConfig

app = create_app(DevConfig)


@app.shell_context_processor
def make_shell_context():
    return {"sa": sa, "so": so}


if __name__ == "__main__":
    app.run(debug=True)
