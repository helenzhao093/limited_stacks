from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import cross_val_score
from sklearn import preprocessing
import pandas as pd
import numpy as np
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_curve, auc

# read datafile with features + target in last column
class Classifier:
    def __init__(self, filename, class_name, df_train_og, df_test_og, df_validate_og):
        
        self.clf = LogisticRegression()
        self.clf_roc = OneVsRestClassifier(LogisticRegression())
        self.accuracy = 0
        self.precision = 0
        self.recall = 0
        self.class_name = class_name

        self.df_train = self.process_discrete_features(df_train_og)
        self.df_test = self.process_discrete_features(df_test_og)
        self.df_validate = self.process_discrete_features(df_validate_og)
        self.df_traintest = pd.concat([self.df_train, self.df_test])

    def process_discrete_features(self, df):
        numeric_data = []
        self.les = {}
        column_names = list(df.columns.values)
        for feature in column_names:
            if feature == self.class_name:
                self.class_labels = np.sort(df[feature].unique())
            if df[feature].dtype != 'int64' or df[feature].dtype != 'float64':
                le = preprocessing.LabelEncoder()
                le.fit(np.sort(df[feature].unique()))
                numeric_data.append(le.transform(df[feature]))
                self.les[feature] = le
            else:
                numeric_data.append(list(df[feature]))
        newdf = pd.DataFrame(np.asarray(numeric_data).T, columns=column_names)
        return newdf

    def classify(self, feature_names):
        X_train, y_train = self.get_X_and_y(feature_names, self.df_train)
        X_traintest, y_traintest = self.get_X_and_y(feature_names, self.df_traintest)
        X_test, y_test = self.get_X_and_y(feature_names, self.df_test)
        X_validation, y_validation = self.get_X_and_y(feature_names, self.df_validate)
        accuracy_train = []
        accuracy_test = []
        accuracy_traintest = []
        accuracy_validation = []

        self.clf.fit(X_train, y_train)
        accuracy_train.append(self.clf.score(X_train, y_train))
        accuracy_test.append(self.clf.score(X_test, y_test)) # testing accuracy
        accuracy_traintest.append(self.clf.score(X_traintest, y_traintest))
        accuracy_validation.append(self.clf.score(X_validation, y_validation))# validation accuracy

        predicted = self.clf.predict(X_test)
        self.proba = self.clf.predict_proba(X_test)
        predicted_train = self.clf.predict(X_test)
        self.init_confusion_matrix(y_test, predicted_train)
        self.get_roc_curve(X_test, y_test)

        self.accuracy_train = round(sum(accuracy_train) * 1.0 / len(accuracy_train), 2)
        #print self.accuracy_train
        self.accuracy = round(sum(accuracy_test) * 1.0 / len(accuracy_test), 2) 
        #print self.accuracy
        self.accuracy_validation = round(sum(accuracy_validation) * 1.0 / len(accuracy_validation), 2)  
        #print self.accuracy_validation

    def get_roc_curve(self, X, y):
        classes = sorted(list(set(y)))
        # print classes
        n_classes = len(classes)
        y_bin = label_binarize(y, classes=classes)
        X_train, X_test, y_train, y_test = train_test_split(X, y_bin, test_size=0.33, random_state=0)
        y_score = self.clf_roc.fit(X_train, y_train).predict_proba(X_test)
        self.rocCurve = dict()
        self.auc = dict()
        for i in range(n_classes):
            class_label = self.class_labels[i]
            fpr, tpr, threshold = roc_curve(y_test[:, i], y_score[:, i], drop_intermediate=False)
            # print threshold
            self.rocCurve[class_label] = []
            for i in range(len(fpr)):
                self.rocCurve[class_label].append([fpr[i], tpr[i]])
            self.auc[class_label] = auc(fpr, tpr)
        #print self.rocCurve

    def init_confusion_matrix(self, y_true, y_pred):
        self.cm = confusion_matrix(y_true, y_pred)
        self.cm_normalized = self.cm.astype('float')/self.cm.sum(axis=1)[:, np.newaxis]
        #print self.cm_normalized

    def set_average_scores(self, accuracy, accuracy_train, precision, recall):
        self.accuracy = self.get_average(accuracy)
        self.precision = self.get_average(precision)
        self.recall = self.get_average(recall)
        self.accuracy_train = self.get_average(accuracy_train)

    def get_average(self, scores):
        return sum(scores)/len(scores)

    def get_X_and_y(self, feature_names, df):
        X = df.loc[:, feature_names]
        y = df.loc[:, self.class_name]
        X = X.as_matrix()
        y = y.as_matrix()
        return X, y
