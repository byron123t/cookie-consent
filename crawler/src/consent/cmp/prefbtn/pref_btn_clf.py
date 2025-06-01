# # ML Models to classify preference button

from typing import Optional
from pathlib import Path
import joblib

from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
import numpy as np
import pandas as pd


class PrefBtnClf:
    """Preference menu activation button classifier."""

    _clf = None

    model_file = Path(__file__).resolve().parent / 'pref_btn_clf.joblib'

    @classmethod
    def get_clf(cls):
        if cls._clf is None:
            cls._clf = cls._load()
        return cls._clf

    @classmethod
    def _load(cls):
        print(f"Load classifier from {cls.model_file}")
        return joblib.load(cls.model_file)

    @classmethod
    def get_top_n(cls, dataset_attrs: pd.DataFrame, dataset_feat: pd.DataFrame, top_n=3, clf=None):
        # Note: testing: eval_btn_clf_notebook -> retrain_and_save_whole_dataset
        if clf is None:
            clf = cls.get_clf()
        return get_top_n(clf, dataset_attrs, dataset_feat, top_n)


def get_pred_probas(clf, probas):
    true_class_idx = np.where(clf.classes_ == True)[0][0]
    return [proba[true_class_idx] for proba in probas]


def predict_dataset(clf, dataset_attrs, dataset_feat):
    dataset_attrs['pred'] = clf.predict(dataset_feat)
    dataset_attrs['proba'] = get_pred_probas(clf, clf.predict_proba(dataset_feat))


def get_top_n(clf, dataset_attrs: pd.DataFrame, dataset_feat, top_n, cutoff_thres: Optional[float]=None):
    predict_dataset(clf, dataset_attrs, dataset_feat)
    if cutoff_thres is not None:
        dataset_attrs = dataset_attrs[dataset_attrs.proba >= cutoff_thres]
    return dataset_attrs.sort_values(by='proba', ascending=False)[:top_n]
