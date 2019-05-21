# Fees related auth_rule
The next authorization rule extends default auth_map from indy-node ([auth_map](https://github.com/hyperledger/indy-node/blob/master/docs/source/add-node.md))
<table class="tg">
  <tr>
    <td>Transaction type</td>
    <td>Action</td>
    <td>Field</td>
    <td>Previous value</td>
    <td>New value</td>
    <td>Who can</td>
    <td>Description</td>
  </tr>

  <tr>
    <td>SET_FEES</td>
    <td>EDIT</td>
    <td>*</td>
    <td>*</td>
    <td>*</td>
    <td>3 TRUSTEEs</td>
    <td>Setting fees for action/actions</td>
  </tr>