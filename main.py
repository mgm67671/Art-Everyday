# website is a package, so everyting in init is run automatically, this is how we import the create_app function
from website import create_app

app = create_app()

# only if we RUN tis file do we execute this line, not import
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

