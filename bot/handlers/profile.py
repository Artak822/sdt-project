import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.fsm.states import RegistrationStates
from bot.keyboards.inline import edit_profile_button
from bot.keyboards.reply import (
    gender_keyboard, looking_for_keyboard, main_menu_keyboard,
    remove_keyboard, keep_keyboard, KEEP_BTN,
)
from bot.services.profile_api import ProfileAPIClient
from bot.services.publisher import publish_profile_complete
from bot.services.redis_cache import invalidate_profile_cache

logger = logging.getLogger(__name__)
router = Router()

GENDER_MAP = {"Мужчина": "male", "Женщина": "female", "Другое": "other"}
LOOKING_FOR_MAP = {"Мужчину": "male", "Женщину": "female", "Не важно": "both"}
GENDER_DISPLAY = {"male": "Мужчина", "female": "Женщина", "other": "Другое"}
LOOKING_FOR_DISPLAY = {"male": "Мужчину", "female": "Женщину", "both": "Всех"}


def _is_keep(text: str) -> bool:
    return text == KEEP_BTN


async def _show_own_profile(target: Message, profile: dict) -> None:
    text = (
        f"<b>👤 Твоя анкета</b>\n\n"
        f"Имя: {profile['name']}\n"
        f"Возраст: {profile['age']}\n"
        f"Пол: {GENDER_DISPLAY.get(profile['gender'], profile['gender'])}\n"
        f"Ищу: {LOOKING_FOR_DISPLAY.get(profile['looking_for'], profile['looking_for'])}\n"
        f"Город: {profile.get('city') or '—'}\n"
        f"О себе: {profile.get('bio') or '—'}"
    )
    keyboard = edit_profile_button()
    if profile.get("photo_id"):
        await target.answer_photo(profile["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await target.answer(text, reply_markup=keyboard)


@router.message(F.text == "👤 Моя анкета")
async def my_profile(message: Message, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    profile = await profile_api.get_profile(message.from_user.id)
    if profile:
        await _show_own_profile(message, profile)
        return

    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer("📝 Заполним анкету!\n\nКак тебя зовут?", reply_markup=remove_keyboard)


async def _start_editing(message: Message, state: FSMContext, profile_api: ProfileAPIClient, user_id: int) -> None:
    profile = await profile_api.get_profile(user_id)
    old = profile or {}
    await state.update_data(is_editing=True, old_profile=old)
    await state.set_state(RegistrationStates.waiting_for_name)
    current = old.get("name", "")
    suffix = f"\n\nСейчас: <b>{current}</b>" if current else ""
    await message.answer(
        f"✏️ Редактируем анкету.\n\nКак тебя зовут?{suffix}",
        reply_markup=keep_keyboard() if old else remove_keyboard,
    )


@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    await callback.answer()
    await _start_editing(callback.message, state, profile_api, callback.from_user.id)


@router.callback_query(F.data == "settings_edit")
async def settings_edit(callback: CallbackQuery, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    await callback.answer()
    await _start_editing(callback.message, state, profile_api, callback.from_user.id)


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if is_editing and _is_keep(text):
        name = data.get("old_profile", {}).get("name", "")
    else:
        name = text
        if not name or len(name) > 50:
            await message.answer("Имя должно быть от 1 до 50 символов. Попробуй ещё раз:")
            return

    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_age)

    if is_editing:
        current = data.get("old_profile", {}).get("age", "")
        suffix = f"\n\nСейчас: <b>{current}</b>" if current else ""
        await message.answer(f"Сколько тебе лет?{suffix}", reply_markup=keep_keyboard())
    else:
        await message.answer("Сколько тебе лет?", reply_markup=remove_keyboard)


@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if is_editing and _is_keep(text):
        age = data.get("old_profile", {}).get("age")
    else:
        try:
            age = int(text)
            if not (14 <= age <= 100):
                raise ValueError
        except ValueError:
            await message.answer("Введи корректный возраст (14–100):")
            return

    await state.update_data(age=age)
    await state.set_state(RegistrationStates.waiting_for_gender)

    if is_editing:
        old_gender = data.get("old_profile", {}).get("gender")
        suffix = f"\n\nСейчас: <b>{GENDER_DISPLAY.get(old_gender, old_gender)}</b>" if old_gender else ""
        await message.answer(f"Укажи свой пол:{suffix}", reply_markup=gender_keyboard(with_keep=True))
    else:
        await message.answer("Укажи свой пол:", reply_markup=gender_keyboard())


@router.message(RegistrationStates.waiting_for_gender)
async def process_gender(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if is_editing and _is_keep(text):
        gender = data.get("old_profile", {}).get("gender")
    else:
        gender = GENDER_MAP.get(text)
        if not gender:
            await message.answer(
                "Выбери один из вариантов:",
                reply_markup=gender_keyboard(with_keep=is_editing),
            )
            return

    await state.update_data(gender=gender)
    await state.set_state(RegistrationStates.waiting_for_looking_for)

    if is_editing:
        old_lf = data.get("old_profile", {}).get("looking_for")
        suffix = f"\n\nСейчас: <b>{LOOKING_FOR_DISPLAY.get(old_lf, old_lf)}</b>" if old_lf else ""
        await message.answer(f"Кого ищешь?{suffix}", reply_markup=looking_for_keyboard(with_keep=True))
    else:
        await message.answer("Кого ищешь?", reply_markup=looking_for_keyboard())


@router.message(RegistrationStates.waiting_for_looking_for)
async def process_looking_for(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if is_editing and _is_keep(text):
        looking_for = data.get("old_profile", {}).get("looking_for")
    else:
        looking_for = LOOKING_FOR_MAP.get(text)
        if not looking_for:
            await message.answer(
                "Выбери один из вариантов:",
                reply_markup=looking_for_keyboard(with_keep=is_editing),
            )
            return

    await state.update_data(looking_for=looking_for)
    await state.set_state(RegistrationStates.waiting_for_city)

    if is_editing:
        current = data.get("old_profile", {}).get("city")
        suffix = f"\n\nСейчас: <b>{current}</b>" if current else ""
        await message.answer(f"Из какого ты города?{suffix}", reply_markup=keep_keyboard())
    else:
        await message.answer("Из какого ты города? (или напиши «пропустить»)", reply_markup=remove_keyboard)


@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if text.lower() == "пропустить" or (is_editing and _is_keep(text)):
        city = data.get("old_profile", {}).get("city") if is_editing else None
    elif len(text) > 100:
        await message.answer("Название города слишком длинное. Попробуй ещё раз:")
        return
    else:
        city = text

    await state.update_data(city=city)
    await state.set_state(RegistrationStates.waiting_for_bio)

    if is_editing:
        current = data.get("old_profile", {}).get("bio")
        suffix = f"\n\nСейчас: <b>{current}</b>" if current else ""
        await message.answer(f"Расскажи немного о себе:{suffix}", reply_markup=keep_keyboard())
    else:
        await message.answer("Расскажи немного о себе (или напиши «пропустить»):", reply_markup=remove_keyboard)


@router.message(RegistrationStates.waiting_for_bio)
async def process_bio(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    if text.lower() == "пропустить" or (is_editing and _is_keep(text)):
        bio = data.get("old_profile", {}).get("bio") if is_editing else None
    elif len(text) > 500:
        await message.answer("Описание слишком длинное (макс. 500 символов). Попробуй ещё раз:")
        return
    else:
        bio = text

    await state.update_data(bio=bio)
    await state.set_state(RegistrationStates.waiting_for_photo)

    if is_editing:
        old_photo_id = data.get("old_profile", {}).get("photo_id")
        if old_photo_id:
            await message.answer_photo(
                old_photo_id,
                caption="Загрузи новое фото или нажми кнопку, чтобы оставить это:",
                reply_markup=keep_keyboard(),
            )
        else:
            await message.answer("Загрузи фото:", reply_markup=keep_keyboard())
    else:
        await message.answer("Загрузи своё фото (или напиши «пропустить»):", reply_markup=remove_keyboard)


@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    await state.update_data(photo_id=message.photo[-1].file_id)
    await _finish_profile(message, state, profile_api)


@router.message(RegistrationStates.waiting_for_photo, F.text)
async def process_photo_skip(message: Message, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    data = await state.get_data()
    is_editing = data.get("is_editing", False)
    text = message.text.strip()

    is_skip = text.lower() == "пропустить" or (is_editing and _is_keep(text))
    if not is_skip:
        await message.answer(
            "Загрузи фото или нажми кнопку:",
            reply_markup=keep_keyboard() if is_editing else remove_keyboard,
        )
        return

    if is_editing:
        old_photo = data.get("old_profile", {}).get("photo_id")
        await state.update_data(photo_id=old_photo)

    await _finish_profile(message, state, profile_api)


async def _finish_profile(message: Message, state: FSMContext, profile_api: ProfileAPIClient) -> None:
    data = await state.get_data()
    is_editing = data.pop("is_editing", False)
    data.pop("old_profile", None)
    await state.clear()

    kwargs = {
        "name": data["name"],
        "age": data["age"],
        "gender": data["gender"],
        "looking_for": data["looking_for"],
        "city": data.get("city"),
        "bio": data.get("bio"),
        "photo_id": data.get("photo_id"),
    }

    if is_editing:
        profile = await profile_api.update_profile(message.from_user.id, **kwargs)
        await invalidate_profile_cache(message.from_user.id)
        success_text = "✅ Анкета обновлена!"
    else:
        profile = await profile_api.create_profile(user_id=message.from_user.id, **kwargs)
        success_text = "✅ Анкета создана! Теперь ты можешь смотреть анкеты других пользователей."

    if not profile:
        await message.answer("Произошла ошибка. Попробуй позже.")
        return

    if not is_editing:
        try:
            await publish_profile_complete(
                profile_id=profile["id"],
                user_id=message.from_user.id,
                **kwargs,
            )
        except Exception as exc:
            logger.warning("Failed to publish profile.complete: %s", exc)

    await message.answer(success_text, reply_markup=main_menu_keyboard())
