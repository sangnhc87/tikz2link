flyctl deploy

flyctl deploy --no-cache

flyctl logs



flyctl secrets set CLOUDINARY_CLOUD_NAME="dfprmep2p"
flyctl secrets set CLOUDINARY_API_KEY="643478257672624"
flyctl secrets set CLOUDINARY_API_SECRET="mlQ9bfc2FkNpZu2OaKOOdu8qRyY"

  cloud_name = os.environ.get('dfprmep2p'),
  api_key = os.environ.get('643478257672624'),
  api_secret = os.environ.get('mlQ9bfc2FkNpZu2OaKOOdu8qRyY'),