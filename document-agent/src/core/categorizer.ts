export class Categorizer {
  private categoryRules: Map<string, RegExp[]>;

  constructor() {
    this.categoryRules = new Map([
      ['aadhaar', [
        /aadhaar/i,
        /aadhar/i,
        /uid/i,
        /unique.?identification/i,
        /\d{4}\s?\d{4}\s?\d{4}/
      ]],
      ['pan', [
        /pan/i,
        /permanent.?account.?number/i,
        /[A-Z]{5}\d{4}[A-Z]/
      ]],
      ['bank_statement', [
        /bank.?statement/i,
        /account.?statement/i,
        /transaction.?history/i,
        /balance/i
      ]],
      ['passport', [
        /passport/i,
        /travel.?document/i,
        /[A-Z]\d{7}/
      ]],
      ['driving_license', [
        /driving.?license/i,
        /driver.?license/i,
        /dl/i,
        /license.?to.?drive/i
      ]],
      ['voter_id', [
        /voter.?id/i,
        /election.?card/i,
        /epic/i,
        /voter.?identity/i
      ]],
      ['insurance', [
        /insurance/i,
        /policy/i,
        /premium/i,
        /coverage/i
      ]],
      ['tax_document', [
        /tax/i,
        /itr/i,
        /income.?tax/i,
        /form.?16/i,
        /tds/i
      ]]
    ]);
  }

  categorize(filename: string, content?: string): string {
    const searchText = `${filename} ${content || ''}`.toLowerCase();

    for (const [category, rules] of this.categoryRules.entries()) {
      for (const rule of rules) {
        if (rule.test(searchText)) {
          return category;
        }
      }
    }

    return 'general';
  }

  addCategory(name: string, rules: RegExp[]): void {
    this.categoryRules.set(name, rules);
  }

  removeCategory(name: string): void {
    this.categoryRules.delete(name);
  }

  getCategories(): string[] {
    return Array.from(this.categoryRules.keys());
  }
}