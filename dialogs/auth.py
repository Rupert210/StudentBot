#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 11:29:54 2024
Диалог аутентификации

@author: ilya@iam.linguanet.ru
"""
from functools import partial

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, User, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

import ssl
from ldap3 import Server, Connection, Tls
from ldap3.core.exceptions import LDAPException, LDAPInvalidCredentialsResult

class AuthDialogSG(StatesGroup):
    start = State()
    usernameState = State()
    passwordState = State()
    successEnd = State()
    authFailState = State()

async def username_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    # Получение id? 
    cache = dialog_manager.middleware_data.get('redis')
    studentId = await cache.get('telegram:{event_from_user.id}')
    
    if studentId != None: # Мы такого знаем!!!
        studentId = int(studentId.decode('ascii'))
    else:
        # Ты кто?..
        studentId = -1
    #print('Current studentid {studentId}')
    dialog_manager.dialog_data['studentId'] = studentId
    return { 'username' : event_from_user.username }

# Проверка на формат логина студента
def username_check(text: str) -> str:
    if all(ch.isdigit() for ch in text[2:]) and text[0:2] == 'st' and len(text) == 12:
        return text
    raise ValueError

async def correct_username_handler(
        message: Message, 
        widget: ManagedTextInput, 
        dialog_manager: DialogManager, 
        text: str) -> None:
    
    dialog_manager.dialog_data['eios_username'] = text
    
    # print (f"Set user:{text} -> {dialog_manager.dialog_data['eios_username']}")
    
    await message.answer(text='Формат логина верный!')
    await dialog_manager.start(state=AuthDialogSG.passwordState)

async def error_username_handler(
        message: Message, 
        widget: ManagedTextInput, 
        dialog_manager: DialogManager, 
        error: ValueError):
    await message.answer(
        text='Сожалеем, у наших студентов таких логинов не бывает. Попробуйте еще раз.'
    )

# Проверка пароля
def password_check( text: str) -> str:
    # проверка - есть ли пароль для проверки?...
    if text != '':
        return text
    raise ValueError

async def correct_password_handler(
        message: Message, 
        widget: ManagedTextInput, 
        dialog_manager: DialogManager, 
        text: str) -> None:

    cache = dialog_manager.middleware_data.get('redis')
    server = dialog_manager.middleware_data.get('ldap_server')
    print ('=======================')
    print ( 'server:',server )
    print ( 'dialog_data:',dialog_manager.dialog_data )
    print ( 'Start_data:',dialog_manager.start_data )
    print ('=======================')
    userName = dialog_manager.dialog_data['eios_username']
    try:
        lconn = Connection(server, user=f'{userName}@iam.linguanet.ru',
                     password=text,
                      auto_bind=True, raise_exceptions=True)
    except LDAPInvalidCredentialsResult:
        raise ValueError
    else:
        student_id = cache.get(f"id:student:{userName}")
        await cache.set( 'telegramid:student:{}', student_id )    
    await dialog_manager.start(state=AuthDialogSG.successEnd)

async def error_password_handler(
        message: Message, 
        widget: ManagedTextInput, 
        dialog_manager: DialogManager, 
        error: ValueError):
    await dialog_manager.start(state=AuthDialogSG.authFailState)

async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()

auth_dialog = Dialog(
    Window(
        Format('Здравствуйте, {username}!'),
        Button(Const('Начать регистрацию ▶️'), id='b_next', on_click=go_next),
        getter=username_getter,
        state=AuthDialogSG.start
    ),
    Window(
        Format('Для получения доступа мы должны получить ваше имя и пароль.'),
        Format('Пожалуйста, ваш логин? (выглядит как st9999999999):'),
        TextInput(
            id='username_input',
            type_factory=username_check,
            on_success=correct_username_handler,
            on_error=error_username_handler,
            ),
        state=AuthDialogSG.usernameState
    ),
    Window(
        Format('Пожалуйста, ваш пароль?'),
        TextInput(
            id='username_input',
            type_factory=password_check,
            on_success=correct_password_handler,
            on_error=error_password_handler,
            ),
        state=AuthDialogSG.passwordState
    ),
    Window(
        Format('Спасибо, можно работать!'),
        state=AuthDialogSG.successEnd
    ),
    Window(
        Format('Увы, не можем получить доступ. Возможно, не тот логин или пароль?'),
        state=AuthDialogSG.authFailState
    ),
)
