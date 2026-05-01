from collections import Counter


def analyze_trends(incidents):

    if not incidents:
        return {
            "message": "No incidents found"
        }

    categories = [i.category for i in incidents]

    counts = Counter(categories)

    top_category = counts.most_common(1)[0]

    return {
        "top_incident_category": top_category[0],
        "count": top_category[1],
        "all_categories": counts
    }