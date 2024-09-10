import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import pickle

# Load quiz results data
data = pd.read_csv('data/quiz_results.csv')

# Check the columns of the data to verify
print(data.columns)
print(data.head())

# Prepare data for Surprise
reader = Reader(rating_scale=(0, 100))  # Assuming scores are between 0 and 100

# Update column names to match those in the CSV file
surprise_data = Dataset.load_from_df(data[['student_id', 'exam_id', 'marks']], reader)

# Split data into train and test sets
trainset, testset = train_test_split(surprise_data, test_size=0.25)

# Train SVD model
algo = SVD()
algo.fit(trainset)

# Save the model
with open('svd_model.pkl', 'wb') as f:
    pickle.dump(algo, f)

print("Model trained and saved.")
