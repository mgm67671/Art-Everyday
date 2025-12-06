# website is a package, so everyting in init is run automatically, this is how we import the create_app function
from website import create_app
import os

app = create_app()

# only if we RUN tis file do we execute this line, not import
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host="0.0.0.0", port=port)

