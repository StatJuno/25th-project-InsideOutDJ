from datasets import Dataset

raw_train_ds = Dataset.from_json("../data/sentiments.train.jsonlines")
raw_val_ds = Dataset.from_json("../data/sentiments.validation.jsonlines")
raw_test_ds = Dataset.from_json("../data/sentiments.test.jsonlines")

# This line prints the description of train_ds
raw_train_ds, raw_val_ds, raw_test_ds