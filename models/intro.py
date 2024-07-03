from bson import ObjectId
import random
import pymongo

class Part1Question:
    def __init__(self, category, question, _id=None):
        self.category = category
        self.question = question
        self._id = _id

    @classmethod
    def from_dict(cls, data):
        return cls(
            category=data.get('category'),
            question=data.get('question'),
            _id=data.get('_id')
        )

    def to_dict(self):
        return {
            'category': self.category,
            'question': self.question
        }

    @classmethod
    def get_all(cls, mongo):
        questions = mongo.db.part1_questions.find()
        return [cls.from_dict(question) for question in questions]

    @classmethod
    def get_by_category(cls, mongo, category):
        questions = mongo.db.part1_questions.find({'category': category})
        return [cls.from_dict(question) for question in questions]

    @classmethod
    def get_by_id(cls, mongo, question_id):
        question = mongo.db.part1_questions.find_one({'_id': ObjectId(question_id)})
        return cls.from_dict(question) if question else None

    def save(self, mongo):
        data = self.to_dict()
        if self._id:
            mongo.db.part1_questions.update_one({'_id': self._id}, {'$set': data})
        else:
            self._id = mongo.db.part1_questions.insert_one(data).inserted_id

    def delete(self, mongo):
        if self._id:
            mongo.db.part1_questions.delete_one({'_id': self._id})

    @classmethod
    def get_questions_by_categories(cls, mongo, categories):
        questions = []
        for category in categories:
            category_questions = mongo.db.part1_questions.find({'category': category}).sort('_id', pymongo.ASCENDING)
            questions.extend([cls.from_dict(question) for question in category_questions])
        return questions

    @classmethod
    def get_random_questions_from_categories(cls, mongo, count=2, questions_per_category=3):
        categories = list(mongo.db.part1_questions.distinct('category'))
        selected_categories = random.sample(categories, count)
        return cls.get_questions_by_categories(mongo, selected_categories)
