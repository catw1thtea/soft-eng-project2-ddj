# Reel Talk

## Product vision statement

Reel Talk is a social app where film lovers can share, discover, and discuss movie reviews.

## User stories

[View our user stories on the Issues page](https://github.com/YOUR-ORG-OR-USER/YOUR-REPO/issues)

## Task boards

[View our sprint task boards on the Projects page](https://github.com/users/catw1thtea/projects/1/views/1)

## Team

- [Jay](https://github.com/Jayyu2005)
- [Danial](https://github.com/catw1thtea)
- [Daniyal](https://github.com/DaniyalMlk)

## Steps necessary to run the software

You need Python 3.10 or newer and git installed.

1. Clone the repository and move into it:

   ```
   git clone https://github.com/YOUR-ORG-OR-USER/YOUR-REPO.git
   cd YOUR-REPO
   ```

2. Create and activate a virtual environment:

   ```
   python3 -m venv venv
   source venv/bin/activate        # Mac/Linux
   venv\Scripts\activate           # Windows
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create your `.env` file by copying the example, then fill in the real values:

   ```
   cp env.example .env             # Mac/Linux
   copy env.example .env           # Windows
   ```

   `MONGO_URI` is the connection string for the team's MongoDB database. Team members can find the real `.env` contents pinned in the team channel. If you are running this on your own, create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas), add a database user, allow your IP address under Network Access, and paste the connection string here. `SECRET_KEY` can be any long random string.

5. Load the starter films into the database (only needed once):

   ```
   python3 seed.py
   ```

6. Start the app:

   ```
   python3 app.py
   ```

7. Open http://127.0.0.1:5000 in your browser. For the intended mobile view, open your browser's developer tools and switch to a phone-sized device view.

Create an account on the sign-up screen to get started.
