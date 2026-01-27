import json
from django.core.management.base import BaseCommand
from core.models import Course, Exam, Question, Choice

class Command(BaseCommand):
    help = "Load MCQ questions from JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str)

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create or get course
        course, _ = Course.objects.get_or_create(title=data["course"])

        exam_data = data["exam"]
        exam, _ = Exam.objects.get_or_create(
            course=course,
            title=exam_data["title"],
            defaults={
                "duration": exam_data.get("duration", 30),
                "total_marks": exam_data.get("total_marks", 0)
            }
        )

        for q in exam_data["questions"]:
            question, created = Question.objects.get_or_create(
                exam=exam,
                text=q["text"]
            )
            if not created:
                self.stdout.write(self.style.WARNING(f"Skipped existing question: {question.text[:50]}"))
                continue

            for choice in q["choices"]:
                Choice.objects.create(
                    question=question,
                    text=choice["text"],
                    is_correct=choice["is_correct"]
                )

            self.stdout.write(self.style.SUCCESS(f"Added question: {question.text[:50]}"))

        self.stdout.write(self.style.SUCCESS("✔ MCQs import completed"))
