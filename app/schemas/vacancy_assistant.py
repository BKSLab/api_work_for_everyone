from pydantic import BaseModel, ConfigDict, Field


class QuestionSchema(BaseModel):
    """Отдельный вопрос анкеты, сгенерированной AI-ассистентом."""

    id: int = Field(..., description="Порядковый номер вопроса.", examples=[1])
    text: str = Field(..., description="Текст вопроса.", examples=["Расскажите об опыте работы с клиентами."])
    required: bool = Field(..., description="Флаг обязательности ответа.", examples=[True])


class QuestionnaireResponseSchema(BaseModel):
    """Анкета, сгенерированная AI-ассистентом по данным вакансии."""

    questions_count: int = Field(..., description="Количество вопросов в анкете.", examples=[5])
    questions: list[QuestionSchema] = Field(..., description="Список вопросов анкеты.")


class QuestionAnswerSchema(BaseModel):
    """Ответ соискателя на отдельный вопрос анкеты."""

    id: int = Field(..., description="Порядковый номер вопроса из анкеты.", examples=[1])
    text: str = Field(..., description="Текст вопроса.", examples=["Расскажите об опыте работы с клиентами."])
    answer: str = Field(
        "",
        description="Ответ соискателя. Может быть пустым для необязательных вопросов.",
        examples=["Три года в сфере продаж, работал с B2B-клиентами."],
    )


class AssistantQuestionnaireRequestSchema(BaseModel):
    """Тело запроса для генерации контента на основе заполненной анкеты."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answers": [
                    {
                        "id": 1,
                        "text": "Расскажите об опыте работы с клиентами.",
                        "answer": "Три года в сфере продаж, работал с B2B-клиентами.",
                    },
                    {
                        "id": 2,
                        "text": "Почему вас привлекает эта вакансия?",
                        "answer": "",
                    },
                ]
            }
        }
    )

    answers: list[QuestionAnswerSchema] = Field(
        ...,
        description="Список ответов соискателя на вопросы анкеты.",
    )


class AssistantTextResponseSchema(BaseModel):
    """Ответ AI-ассистента в виде HTML-текста (сопроводительное письмо или рекомендации по резюме)."""

    result: str = Field(
        ...,
        description="HTML-текст сгенерированного контента.",
    )
