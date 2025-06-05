# # ML Models to classify preference button

from typing import Optional
import joblib

from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
import numpy as np
import pandas as pd

from consent.util.default_path import create_data_dir, get_data_dir


class PrefBtnClf:
    """Preference menu activation button classifier."""

    _clf = None

    # Same with eval_btn_clf_notebook.
    # model_file = get_data_dir("2021-08-06") / 'pref_btn_clf.joblib'
    model_file = create_data_dir("2022-05-21") / 'pref_btn_clf.joblib'

    @classmethod
    def get_clf(cls):
        if cls._clf is None:
            cls._clf = cls._load()
        return cls._clf

    @classmethod
    def _save(cls, model):
        joblib.dump(model, cls.model_file)
        print(f"Saved classifier to {cls.model_file}")

    @classmethod
    def _load(cls):
        print(f"Load classifier from {cls.model_file}")
        return joblib.load(cls.model_file)

    @classmethod
    def train_and_save(cls, train_feat, train_labels, save=False, aclf=None):
        def _get_clf():
            """Get conventional classifiers with no hyper search."""
            clf = RandomForestClassifier(n_estimators=100, random_state=1025) #, class_weight={False: 1, True: 2}) # other classifiers always predict 0 due to imbalance
            # clf = SVC(probability=True)
            # clf = MLPClassifier(hidden_layer_sizes=(100,), random_state=1025) #, shuffle=False)  # Turn off shuffle to make result consistent (predict 1-by-1 in train_eval_btn_clf_notebook)
            # clf = RandomForestClassifier(n_estimators=200, random_state=1025)
            # clf = RandomForestClassifier(n_estimators=200, random_state=1025, class_weight='balanced_subsample')
            # clf = imbalance.BalancedRandomForestClassifier(n_estimators=100, random_state=1025)
            # clf = xgb.XGBClassifier(n_estimators=200, random_state=1025)
            return clf

        clf = aclf if aclf is not None else _get_clf()
        clf.fit(train_feat, train_labels)

        if save:
            cls._save(clf)

        return clf

    @classmethod
    def get_top_n(cls, dataset_attrs: pd.DataFrame, dataset_feat: pd.DataFrame, top_n=3, clf=None):
        # Note: testing: eval_btn_clf_notebook -> retrain_and_save_whole_dataset
        if clf is None:
            clf = cls.get_clf()
        return get_top_n(clf, dataset_attrs, dataset_feat, top_n)


def get_pred_probas(clf, probas):
    true_class_idx = np.where(clf.classes_ == True)[0][0]
    # print(f'{true_class_idx=}')
    return [proba[true_class_idx] for proba in probas]


def predict_dataset(clf, dataset_attrs, dataset_feat):
    dataset_attrs['pred'] = clf.predict(dataset_feat)
    dataset_attrs['proba'] = get_pred_probas(clf, clf.predict_proba(dataset_feat))


def get_top_n(clf, dataset_attrs: pd.DataFrame, dataset_feat, top_n, cutoff_thres: Optional[float]=None):
    predict_dataset(clf, dataset_attrs, dataset_feat)
    if cutoff_thres is not None:
        dataset_attrs = dataset_attrs[dataset_attrs.proba >= cutoff_thres]
    return dataset_attrs.sort_values(by='proba', ascending=False)[:top_n]
