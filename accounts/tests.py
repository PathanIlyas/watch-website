import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from otp_auth.models import OTPVerification


User = get_user_model()


@override_settings(
    DEBUG=True,
    SMS_PROVIDER='console',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class AuthenticationFlowTests(TestCase):
    def test_register_verify_auto_login_then_password_login_with_phone(self):
        with patch('otp_auth.utils.generate_otp', return_value='123456'):
            register_response = self.client.post(reverse('register'), {
                'full_name': 'New Customer',
                'username': 'newcustomer',
                'email': 'new@example.com',
                'phone': '9876543210',
                'password': 'StrongPass123!',
                'password2': 'StrongPass123!',
            })

        self.assertEqual(register_response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

        phone = '+919876543210'
        verify_response = self.client.post(
            reverse('register_verify_otp'),
            data=json.dumps({'otp': '123456', 'phone': phone}),
            content_type='application/json',
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertTrue(verify_response.json()['success'])
        user = User.objects.get(email='new@example.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
        self.assertTrue(user.check_password('StrongPass123!'))

        self.client.get(reverse('logout'))

        login_response = self.client.post(reverse('login'), {
            'username': 'newcustomer',
            'password': 'StrongPass123!',
        })

        self.assertEqual(login_response.status_code, 302)
        self.assertNotIn('pending_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_password_login_accepts_username_and_email_without_otp(self):
        user = User.objects.create_user(
            username='classicuser',
            email='classic@example.com',
            full_name='Classic Customer',
            phone_number='+919876543219',
            password='StrongPass123!',
        )

        username_response = self.client.post(reverse('login'), {
            'username': 'classicuser',
            'password': 'StrongPass123!',
        })

        self.assertEqual(username_response.status_code, 302)
        self.assertNotIn('pending_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        self.client.get(reverse('logout'))

        email_response = self.client.post(reverse('login'), {
            'username': 'CLASSIC@example.com',
            'password': 'StrongPass123!',
        })

        self.assertEqual(email_response.status_code, 302)
        self.assertNotIn('pending_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        self.client.get(reverse('logout'))

        name_response = self.client.post(reverse('login'), {
            'username': 'classic customer',
            'password': 'StrongPass123!',
        })

        self.assertEqual(name_response.status_code, 302)
        self.assertNotIn('pending_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_otp_only_login_sets_pending_user_and_unknown_phone_does_not_create_user(self):
        user = User.objects.create_user(
            username='otp@example.com',
            email='otp@example.com',
            phone_number='+919876543211',
            password='StrongPass123!',
        )

        with patch('otp_auth.utils.generate_otp', return_value='111222'):
            response = self.client.post(
                reverse('login_send_otp'),
                data=json.dumps({'phone': '9876543211'}),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['pending_user_id'], user.id)

        verify_response = self.client.post(
            reverse('login_verify_otp'),
            data=json.dumps({'otp': '111222', 'phone': '+919876543211'}),
            content_type='application/json',
        )

        self.assertTrue(verify_response.json()['success'])
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        self.client.get(reverse('logout'))
        unknown_response = self.client.post(
            reverse('login_send_otp'),
            data=json.dumps({'phone': '9876543212'}),
            content_type='application/json',
        )

        self.assertEqual(unknown_response.status_code, 404)
        self.assertIn('Please register first', unknown_response.json()['error'])
        self.assertFalse(User.objects.filter(phone_number='+919876543212').exists())
        self.assertFalse(OTPVerification.objects.filter(phone='+919876543212').exists())
