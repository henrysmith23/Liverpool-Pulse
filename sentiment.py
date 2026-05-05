from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def score_text(text):
    score = analyzer.polarity_scores(text)["compound"]
    return (score + 1) * 50
