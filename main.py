# website is a package, so everyting in init is run automatically, this is how we import the create_app function
import os
from website import create_app

app = create_app()

# only if we RUN tis file do we execute this line, not import
if __name__ == '__main__':
    # Use Cloud Run's PORT env var in production, fallback to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host="0.0.0.0", port=port)

